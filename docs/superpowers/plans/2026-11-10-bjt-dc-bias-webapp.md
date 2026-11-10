# BJT DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App หลายไฟล์ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วคำนวณ DC Operating Point ของวงจร BJT Voltage-Divider Bias ด้วย Python Backend พร้อม validation, region warning และ automated tests

**Architecture:** แยก 3 ชั้นชัดเจน — `dc_bias.py` (สมการบริสุทธิ์ ไม่รู้จัก HTTP) → `app.py` (Flask routes + form parsing) → `templates/index.html` (Jinja2, ไม่มีสมการ) โดยมี `static/style.css` และ `tests/` แยกต่างหาก

**Tech Stack:** Python 3.15.2, Flask 3.1.3, Jinja2, unittest (ไม่ใช้ pytest เพื่อให้ตรงคำสั่งในเอกสาร Lab)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.15.2, `Flask==3.1.3` (pin ใน requirements.txt)
- หน่วยภายในโมดูล: **V, Ω, A** ทั้งหมด; แปลง kΩ→Ω ที่ชั้น `parse_form` เท่านั้น
- แสดงผล: แรงดัน 3 ตำแหน่งทศนิยม (V), กระแส 3 ตำแหน่ง (mA)
- `VCE_SAT = 0.3` V (ค่าคงที่ใน `dc_bias.py`)
- **ห้าม hardcode ผลลัพธ์ใน template** — ตัวเลขทุกตัวต้องมาจาก `BiasResult`
- ข้อความ UI: ภาษาไทย + ศัพท์เทคนิคอังกฤษ; ชื่อ field/ตัวแปรเป็นอังกฤษ
- **ห้ามรัน `git commit` / `git push`** — ผู้ใช้ commit ผ่าน **GitHub Desktop** เท่านั้น; agent ทำได้แค่แก้ไฟล์และรายงานไฟล์ที่เปลี่ยน + ข้อความ commit ที่แนะนำ
- Path เป็น Windows (`\`); รันคำสั่งจาก root ของ repo
- ค่า default ของฟอร์ม: 12 V, 100 kΩ, 22 kΩ, 2.2 kΩ, 1 kΩ, β=100, VBE=0.70 V

## Review Focus

อินพุต/สภาวะที่ spec ไม่ได้เขียนไว้ชัด แต่มีโอกาสทำให้โปรแกรมพังหรือให้ผลผิด — ทุกข้อมี test ใน task ที่ระบุ:

1. **ฟอร์มส่งมาไม่ครบ field** (เช่น POST มีแค่ `vcc`) → ต้องได้ error ที่อ่านรู้เรื่อง ไม่ใช่ `KeyError`/500 (Task 2)
2. **ตัวเลขมี comma หรือช่องว่าง** (`"1,000"`, `" 100 "`) → ต้องไม่ crash; ค่าที่มี comma ให้แจ้ง error (Task 2)
3. **`VTH < VBE`** → IC ต้องไม่ติดลบ; ต้องรายงาน `cutoff` (Task 3)
4. **`VCE < 0.3 V`** → ต้องรายงาน `saturation` + warning ไม่ใช่ `active` (Task 3)
5. **β ต่ำมาก (β=1) หรือ RC/RE สุดขั้ว** → ต้องคืนค่าจำกัด (finite) ไม่ crash/หารศูนย์ (Task 1, Task 3)
6. **ค่าที่ไม่ใช่ตัวเลข** (`"abc"`, ค่าว่าง) → error list ไม่ raise exception (Task 2)

---

### Task 1: โครงโปรเจกต์ + สมการ DC Bias หลัก

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces:
  - `BiasInputs(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float)` — frozen dataclass, หน่วย SI
  - `BiasResult(vth, rth, ib, ic, ie, vb, ve, vc, vce: float, region: str, warnings: list[str])` — frozen dataclass
  - `calculate_dc_bias(inputs: BiasInputs) -> BiasResult`

- [ ] **Step 1: สร้าง `requirements.txt` และ `.gitignore`**

`requirements.txt`:
```
Flask==3.1.3
```

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
```

- [ ] **Step 2: เขียน failing test — ค่าอ้างอิงวงจร**

`tests/test_dc_bias.py`:
```python
import math
import unittest
from dc_bias import BiasInputs, calculate_dc_bias


class TestReferenceOperatingPoint(unittest.TestCase):
    def setUp(self):
        self.inputs = BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        )

    def test_known_reference_values(self):
        r = calculate_dc_bias(self.inputs)
        self.assertAlmostEqual(r.vth, 2.1639, places=3)
        self.assertAlmostEqual(r.rth, 18_032.8, delta=1.0)
        self.assertAlmostEqual(r.ib, 12.298e-6, delta=1e-8)
        self.assertAlmostEqual(r.ic, 1.2298e-3, delta=1e-7)
        self.assertAlmostEqual(r.ie, 1.2422e-3, delta=1e-7)
        self.assertAlmostEqual(r.ve, 1.2422, places=3)
        self.assertAlmostEqual(r.vb, 1.9422, places=3)
        self.assertAlmostEqual(r.vc, 9.2943, places=3)
        self.assertAlmostEqual(r.vce, 8.0522, places=3)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, [])

    def test_extreme_beta_stays_finite(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=1.0, vbe=0.70,
        ))
        for value in (r.ib, r.ic, r.ie, r.vce):
            self.assertTrue(math.isfinite(value))
```

- [ ] **Step 3: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 4: implement `dc_bias.py` — dataclasses + `calculate_dc_bias`**

สร้าง `BiasInputs` / `BiasResult` เป็น `@dataclass(frozen=True)` และ implement สมการตาม Spec §7 ทุกบรรทัด:
`vth`, `rth`, `ib`, `ic`, `ie`, `ve`, `vb`, `vc`, `vce`
ขั้นนี้ให้ `region = "active"` และ `warnings = []` ไว้ก่อน (Task 3 จะมาแทนที่)
ถ้า `ib < 0` ให้ `ic = ie = 0.0` และ `vc = vcc` (กันค่าติดลบ)

- [ ] **Step 5: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 2 tests

- [ ] **Step 6: Commit (GitHub Desktop)**

แจ้งผู้ใช้: เปิด GitHub Desktop → ตรวจไฟล์ `requirements.txt`, `.gitignore`, `dc_bias.py`, `tests/test_dc_bias.py` → Summary: `feat: add DC bias calculation core`

---

### Task 2: Form parsing + Validation + การแปลงหน่วย

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasInputs` จาก Task 1
- Produces:
  - `parse_form(form: Mapping[str, str]) -> tuple[BiasInputs | None, list[str]]`
  - `validate_inputs(inputs: BiasInputs) -> list[str]`
  - ชื่อ field ที่ฟอร์มต้องส่ง: `vcc`, `r1`, `r1_unit`, `r2`, `r2_unit`, `rc`, `rc_unit`, `re`, `re_unit`, `beta`, `vbe`
  - `*_unit` รับค่า `"ohm"` หรือ `"kohm"` (ค่าเริ่มต้นถ้าไม่ส่งมา: `"kohm"`)

- [ ] **Step 1: เขียน failing tests — การแปลงหน่วย + validation**

เพิ่มใน `tests/test_dc_bias.py`:
```python
from dc_bias import parse_form


class TestParseForm(unittest.TestCase):
    BASE = {
        "vcc": "12", "beta": "100", "vbe": "0.70",
        "r1": "100", "r1_unit": "kohm",
        "r2": "22", "r2_unit": "kohm",
        "rc": "2.2", "rc_unit": "kohm",
        "re": "1", "re_unit": "kohm",
    }

    def test_kohm_converted_to_ohm(self):
        inputs, errors = parse_form(self.BASE)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(inputs.r1, 100_000.0)

    def test_ohm_unit_is_not_scaled(self):
        form = dict(self.BASE, r1="100000", r1_unit="ohm")
        inputs, errors = parse_form(form)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(inputs.r1, 100_000.0)

    def test_non_numeric_returns_error_not_exception(self):
        form = dict(self.BASE, r1="abc")
        inputs, errors = parse_form(form)
        self.assertIsNone(inputs)
        self.assertTrue(any("R1" in e for e in errors))

    def test_missing_field_returns_error_not_keyerror(self):
        form = {"vcc": "12"}
        inputs, errors = parse_form(form)
        self.assertIsNone(inputs)
        self.assertTrue(len(errors) >= 6)

    def test_comma_in_number_is_reported(self):
        form = dict(self.BASE, r1="1,000")
        inputs, errors = parse_form(form)
        self.assertIsNone(inputs)
        self.assertTrue(any("R1" in e for e in errors))

    def test_whitespace_is_tolerated(self):
        form = dict(self.BASE, r1=" 100 ")
        inputs, errors = parse_form(form)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(inputs.r1, 100_000.0)

    def test_non_positive_values_are_rejected(self):
        for field, value in [("r1", "0"), ("beta", "0"), ("vcc", "-1")]:
            form = dict(self.BASE, **{field: value})
            inputs, errors = parse_form(form)
            self.assertIsNone(inputs, msg=field)
            self.assertTrue(errors, msg=field)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ImportError: cannot import name 'parse_form'`

- [ ] **Step 3: implement `parse_form` + `validate_inputs`**

- `parse_form` อ่านทุก key ด้วย `form.get(name)` (ห้ามใช้ `form[name]`), `strip()` ค่า, แปลงด้วย `float()`
- ถ้าแปลงไม่ได้ → เก็บ error ภาษาไทยระบุชื่อ field เช่น `"R1 ต้องเป็นตัวเลข"` แล้วไปต่อ field ถัดไป (รวบรวม error ทั้งหมด ไม่หยุดที่ตัวแรก)
- คูณ `1000` เมื่อ `*_unit == "kohm"`
- เรียก `validate_inputs()` ต่อ; ถ้ามี error คืน `(None, errors)`
- `validate_inputs` ตรวจ: `vcc > 0`, `r1 > 0`, `r2 > 0`, `rc > 0`, `re > 0`, `beta > 0`, `vbe > 0`, และ `(r1 + r2) > 0`
- ข้อความ error ต้องเป็นรูปแบบนี้เป๊ะ (Task 4 assert ข้อความนี้):
  - แปลงตัวเลขไม่ได้: `f"{label} ต้องเป็นตัวเลข"` → label ∈ `VCC, R1, R2, RC, RE, β, VBE`
  - ค่าไม่อยู่ในช่วง: `f"{label} ต้องเป็นค่ามากกว่าศูนย์"`

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 9 tests

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: add form parsing, unit conversion and validation`

---

### Task 3: Region detection + Warnings

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `calculate_dc_bias()` จาก Task 1
- Produces: `BiasResult.region` ∈ `{"active", "cutoff", "saturation"}` และ `BiasResult.warnings: list[str]` (ข้อความไทย)

- [ ] **Step 1: เขียน failing tests — cutoff / saturation**

```python
class TestOperatingRegion(unittest.TestCase):
    def test_cutoff_when_vth_below_vbe(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=1_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        ))
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.vc, 12.0)
        self.assertTrue(any("cutoff" in w.lower() for w in r.warnings))

    def test_saturation_when_vce_below_threshold(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=10_000.0, re=1_000.0, beta=100.0, vbe=0.70,
        ))
        self.assertEqual(r.region, "saturation")
        self.assertTrue(r.vce < 0.3)
        self.assertTrue(any("saturation" in w.lower() for w in r.warnings))

    def test_active_region_has_no_warnings(self):
        r = calculate_dc_bias(BiasInputs(
            vcc=12.0, r1=100_000.0, r2=22_000.0,
            rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
        ))
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, [])
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — region ยังเป็น `"active"` ทุกกรณี

- [ ] **Step 3: implement การตัดสิน region**

ใน `calculate_dc_bias` หลังคำนวณค่าทั้งหมด:
- ถ้า `vth <= vbe` → `region="cutoff"`, `ic=ie=0.0`, `vc=vcc`, `vce=vcc-ve`, warning: `"วงจรอยู่ในช่วง Cutoff — แบบจำลอง Forward-Active ใช้ไม่ได้"` (ใช้ `ve` ที่คำนวณได้จาก IB=0 คือ 0)
- elif `vce < VCE_SAT` → `region="saturation"`, warning: `"VCE ต่ำกว่า 0.3 V — อาจอยู่ในช่วง Saturation ผลจากแบบจำลอง Forward-Active ไม่น่าเชื่อถือ"`
- else → `region="active"`, `warnings=[]`

- [ ] **Step 4: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 12 tests

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: add operating region detection and warnings`

---

### Task 4: Flask app + Template + CSS

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `parse_form()`, `calculate_dc_bias()` จาก Task 1–3
- Produces:
  - `app` (Flask instance) ที่ `app.py` ระดับ module
  - `GET /` → 200, template `index.html`, context: `form`, `result=None`, `errors=[]`
  - `POST /calculate` → 200 + `result` เมื่อถูกต้อง / 400 + `errors` เมื่อผิด
  - Jinja filter `fmt` สำหรับจัดรูปตัวเลข

- [ ] **Step 1: เขียน failing tests — HTTP**

`tests/test_web.py`:
```python
import unittest
from app import app


class TestWebRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'name="vcc"', resp.data)
        self.assertIn(b'name="r1_unit"', resp.data)

    def test_post_valid_inputs_shows_result(self):
        resp = self.client.post("/calculate", data={
            "vcc": "12", "beta": "100", "vbe": "0.70",
            "r1": "100", "r1_unit": "kohm",
            "r2": "22", "r2_unit": "kohm",
            "rc": "2.2", "rc_unit": "kohm",
            "re": "1", "re_unit": "kohm",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VCE".encode(), resp.data)
        self.assertIn(b"8.052", resp.data)

    def test_post_invalid_inputs_returns_400_with_error(self):
        resp = self.client.post("/calculate", data={
            "vcc": "12", "beta": "0", "vbe": "0.70",
            "r1": "100", "r1_unit": "kohm",
            "r2": "22", "r2_unit": "kohm",
            "rc": "2.2", "rc_unit": "kohm",
            "re": "1", "re_unit": "kohm",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ต้องเป็นค่ามากกว่าศูนย์".encode(), resp.data)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: implement `app.py`**

- `DEFAULTS = {"vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm", "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm", "beta": "100", "vbe": "0.70"}`
- `@app.template_filter("fmt")` → `f"{value:.3f}"`
- `index()` คืน `render_template("index.html", form=DEFAULTS, result=None, errors=[])`
- `calculate()` → `parse_form(request.form)`; ถ้า error → `render_template(...), 400`; ถ้าผ่าน → `calculate_dc_bias()` แล้ว render 200 พร้อม `form=request.form`
- ต้องไม่ throw เมื่อ `request.form` ว่าง

- [ ] **Step 4: implement `templates/index.html`**

- ฟอร์ม `method="post" action="/calculate"`, ทุก input มี `name` ตรงกับ Task 2
- ช่องตัวต้านทาน 4 ช่อง: `<input type="number" step="any" name="r1">` + `<select name="r1_unit"><option value="kohm">kΩ</option><option value="ohm">Ω</option></select>` (default = `kohm`; คงค่าที่ผู้ใช้เลือกด้วย `form.get(...)`)
- กล่อง error (แดง) และ warning (เหลือง) แสดงเฉพาะเมื่อมีค่า
- เมื่อมี `result`: การ์ดหลัก VB, VE, VC, VCE (V) + IC (mA) และตารางรอง IB, IE, VTH, RTH; badge region 3 สี
- **ห้ามใส่ตัวเลขผลลัพธ์แบบ literal ใด ๆ** — ใช้ `{{ result.vce|fmt }}` เท่านั้น

- [ ] **Step 5: implement `static/style.css`**

- CSS variables โทนน้ำเงิน-เทา, การ์ดมุมโค้ง, grid 2 คอลัมน์เมื่อกว้าง ≥ 900px, 1 คอลัมน์บนมือถือ, ฟอนต์ `Tahoma, "Noto Sans Thai", sans-serif`

- [ ] **Step 6: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests

- [ ] **Step 7: ทดลองเปิดเว็บจริง**

Run: `python -m flask --app app run --debug`
Expected: เปิด `http://127.0.0.1:5000/` เห็นฟอร์ม, กด Calculate แล้วเห็น VCE ≈ 8.052 V และ badge `Active`

- [ ] **Step 8: Commit (GitHub Desktop)**

Summary: `feat: add Flask routes, Jinja template and styles`

---

### Task 5: README + เอกสารประกอบ + ตรวจรับรอบสุดท้าย

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–4
- Produces: เอกสารที่ทำให้ A7 (reproducibility) ผ่าน

- [ ] **Step 1: เขียน `README.md`**

ต้องมี: ภาพรวมโปรเจกต์, วิธีติดตั้ง (`python -m venv .venv`, activate ตาม OS, `pip install -r requirements.txt`), วิธีรัน (`python -m flask --app app run --debug`), วิธีรัน tests (`python -m unittest discover -s tests -v`), ค่า default ที่ใช้ทดสอบ, และสมมติฐาน Forward-Active + ข้อจำกัด

- [ ] **Step 2: เขียน `AGENTS.md`**

กติกาสำหรับ AI agent: ห้าม hardcode ผลลัพธ์, สมการอยู่ใน `dc_bias.py` เท่านั้น, ห้าม commit แทนผู้ใช้, รัน tests ก่อนอ้างว่างานเสร็จ

- [ ] **Step 3: เขียน `docs/validation.md`**

ตารางเทียบค่าที่ได้จากเว็บกับค่าคำนวณมือ (VTH 2.164, RTH 18.03 kΩ, IB 12.30 µA, IC 1.230 mA, IE 1.242 mA, VE 1.242 V, VB 1.942 V, VC 9.294 V, VCE 8.052 V) + tolerance ที่ใช้ + ผลทดสอบกรณี invalid/cutoff/saturation

- [ ] **Step 4: เขียน `docs/design-note.md`**

สรุปสถาปัตยกรรม 3 ชั้น, เหตุผลที่แยก `dc_bias.py` ออกจาก `app.py`, และทางเลือกที่ตัดทิ้ง

- [ ] **Step 5: เขียน `docs/reflection.md` เป็นโครงให้ผู้ใช้เติม**

หัวข้อ: อะไรที่ AI ช่วยได้/ไม่ได้, จุดที่ต้องตรวจเอง, สิ่งที่จะทำต่างในสัปดาห์หน้า (เว้นเนื้อหาให้ผู้ใช้เขียนเอง ห้ามแต่งแทน)

- [ ] **Step 6: ตรวจรับ A1–A7**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests

ตรวจด้วยตา: GET / = 200, กรอกค่าผิดเห็น error, กรอกค่า cutoff/saturation เห็น warning, ไม่มีตัวเลข hardcode ใน `templates/index.html` (`Select-String -Path templates\index.html -Pattern "8\.05|1\.23"` ต้องไม่เจอ)

- [ ] **Step 7: Commit (GitHub Desktop)**

Summary: `docs: add README, validation notes and lab documentation`

- [ ] **Step 8: Push**

ผู้ใช้กด **Push origin** ใน GitHub Desktop แล้วคัดลอก URL + commit SHA ส่ง Moodle
