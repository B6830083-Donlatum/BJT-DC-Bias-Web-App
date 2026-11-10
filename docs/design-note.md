# Design Note — BJT DC Bias Web App (Lab 02)

วันที่: 2026-11-10
รายวิชา: ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
อ้างอิง Design ที่อนุมัติแล้ว: `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## 1. ภาพรวมสถาปัตยกรรม

แยกโค้ดเป็น 3 ชั้นชัดเจน เพื่อให้ "สมการ" กับ "การรับส่ง HTTP" ไม่ปนกัน

```
เบราว์เซอร์
   │  GET /  ·  POST /calculate (form data)
   ▼
app.py                  ← HTTP layer: อ่าน request.form, เลือก template, ใส่ status code
   │  parse_form() → BiasInputs | errors
   │  calculate_dc_bias() → BiasResult
   ▼
dc_bias.py              ← Engineering layer: สมการ + validation (pure functions)
   │  BiasResult (V, Ω, A)
   ▼
templates/index.html    ← Presentation layer: Jinja2 แสดงค่าจาก BiasResult เท่านั้น
static/style.css        ← หน้าตา/responsive
```

### ชั้นที่ 1 — `dc_bias.py` (Engineering core)

- เป็น **pure functions** ไม่มี side effect ไม่แตะ Flask/HTTP/HTML
- หน่วยภายในเป็น SI ทั้งหมด: **V, Ω, A**
- ประกอบด้วย
  - `BiasInputs` / `BiasResult` — frozen dataclass
  - `calculate_dc_bias()` — สมการ Forward-Active + ตัดสิน operating region
  - `validate_inputs()` — ตรวจช่วงค่า (ต้องมากกว่าศูนย์)
  - `parse_form()` — แปลงข้อความจากฟอร์มเป็น SI + แปลง kΩ → Ω
- ค่าคงที่ `VCE_SAT = 0.3` V อยู่ที่นี่ที่เดียว

### ชั้นที่ 2 — `app.py` (HTTP layer)

- มีแค่ 2 route: `GET /` และ `POST /calculate`
- ไม่มีสมการใด ๆ — เรียก `parse_form()` แล้ว `calculate_dc_bias()` ตามลำดับ
- Validation ฝั่ง server เป็นแหล่งความจริง (HTML `required` เป็นเพียง UX)
- ไม่ใช้ session / ไม่มี state ฝั่ง server
- Jinja filter `fmt` ใช้จัดทศนิยม 3 ตำแหน่ง

### ชั้นที่ 3 — `templates/index.html` + `static/style.css`

- Template **ไม่มีตัวเลขผลลัพธ์แบบ hardcode** ทุกค่ามาจาก `result.*`
- ใช้ `{{ result.vce|fmt }}` ไม่ใช่ `8.052`
- Badge region เปลี่ยนสีตาม `result.region` (active / cutoff / saturation)
- Responsive: 1 คอลัมน์บนมือถือ, 2 คอลัมน์เมื่อกว้าง ≥ 760px

## 2. เหตุผลที่แยก `dc_bias.py` ออกจาก `app.py`

| เหตุผล | ผลที่ได้ |
|--------|----------|
| สมการต้องทดสอบได้โดยไม่ต้องเปิดเว็บ | `tests/test_dc_bias.py` เรียกฟังก์ชันตรง ๆ เร็วและ deterministic |
| เกณฑ์ A2/A6 บังคับให้คำนวณที่ Python backend | แยกชั้นทำให้เห็นชัดว่าไม่มี JavaScript คำนวณผล |
| ต่อยอด W3 (bias แบบอื่น) ได้ง่าย | เพิ่มโมดูลสมการใหม่โดยไม่แตะ HTTP layer |
| ป้องกันการ hardcode | Template ไม่มีทางเข้าถึงตัวเลขได้นอกจากผ่าน `BiasResult` |

## 3. การตัดสิน Operating Region

| เงื่อนไข | Region | การกระทำ |
|----------|--------|----------|
| `VTH ≤ VBE` (IB ≤ 0) | `cutoff` | บังคับ `IB = IC = IE = 0`, `VC = VCC` + warning |
| `VCE < 0.3 V` | `saturation` | แสดงค่าตามสมการ + warning ว่า model ไม่น่าเชื่อถือ |
| อื่น ๆ | `active` | แสดงผลปกติ ไม่มี warning |

หมายเหตุ: ตรวจ `cutoff` ก่อน `saturation` เสมอ เพราะถ้าวงจร cutoff ค่า `VCE` ที่คำนวณได้จะไม่มีความหมายทางกายภาพ

## 4. ทางเลือกที่พิจารณาแล้วตัดทิ้ง

| ทางเลือก | เหตุผลที่ตัดทิ้ง |
|----------|------------------|
| App factory + Blueprint | เพิ่ม indirection โดยไม่ได้คะแนนเพิ่มในคาบนี้ (refactor ทีหลังได้) |
| Single-file Flask | แยกสมการ/HTTP ไม่ชัด เสี่ยง hardcode และทดสอบยาก |
| คำนวณด้วย JavaScript ฝั่ง client | ผิดเกณฑ์ A2 (ต้องเป็น Python backend) |
| แยก `_results.html` เป็น partial | ใช้ `{% if result %}` ในไฟล์เดียวลดจำนวนไฟล์ ลดความซับซ้อน |
| ใช้ pytest | เอกสาร Lab ระบุ `unittest` — ใช้ `unittest` ตรงตามโจทย์ |

## 5. สมมติฐานของแบบจำลอง

- ใช้ **Forward-Active approximation**: β คงที่, VBE คงที่
- ไม่คิด Early effect, อุณหภูมิ, ความคลาดเคลื่อนของอุปกรณ์
- ไม่ใช่ SPICE — เป็นการคำนวณเชิงวิเคราะห์ตามสมการใน §7 ของ Design
- ผลนอก Forward Active ต้องอ่านพร้อม warning เสมอ

## 6. การตัดสินใจระหว่างทาง (rulings)

| เรื่อง | การตัดสิน | เหตุผล |
|--------|------|--------|
| ตำแหน่งแปลงหน่วย | ที่ `parse_form()` เท่านั้น | โมดูลสมการรับ SI ล้วน ลดโอกาสผิดหน่วย |
| ข้อความ error | `"{label} ต้องเป็นตัวเลข"` / `"{label} ต้องเป็นค่ามากกว่าศูนย์"` | ตรงกันระหว่าง backend และ test ฝั่งเว็บ |
| ฟอร์มส่งมาไม่ครบ | รวบรวม error ทุก field แล้วคืน `(None, errors)` | หลีกเลี่ยง `KeyError`/HTTP 500 |
| ตัวเลขมี comma (`"1,000"`) | นับเป็น "ไม่ใช่ตัวเลข" และแจ้ง error | ไม่เดาเจตนาผู้ใช้ |
| β ต่ำมาก (β=1) | คืนค่าจำกัด (finite) ตามสมการ | ไม่หารศูนย์เพราะมี `(β+1)·RE` และ `RTH` เป็นบวก |
| แยก `validate_inputs` ออกจาก `parse_form` | `parse_form(form) → (BiasInputs \| None, errors)` + `validate_inputs(BiasInputs) → errors` | spec §7 เขียนรวมเป็นฟังก์ชันเดียว แต่การแยกทำให้แปลงหน่วย/แปลงชนิด กับตรวจช่วงค่า ทดสอบแยกกันได้ — ผลลัพธ์เทียบเท่า |
| ค่า `nan` / `inf` | ปฏิเสธด้วย "ต้องเป็นจำนวนจำกัด" | `float("nan")` แปลงผ่านและ `nan <= 0` เป็น False จึงต้องตรวจ `math.isfinite()` แยก |
| `VB` ในช่วง Cutoff | ใช้ `VB = VTH` | ไม่มีกระแสเบส → เบสอยู่ที่แรงดัน Thévenin; `VE + VBE` ใช้ได้เฉพาะ Forward Active |
| ให้ agent merge + push แทนผู้ใช้ | ทำแทนตามคำสั่งผู้ใช้ (2026-11-10) | กติกา AGENTS.md ข้อ 3 กำหนดให้ commit/push ผ่าน GitHub Desktop เท่านั้น แต่ผู้ใช้สั่งชัดเจนให้ agent ปิดงานให้ (Publish branch เสร็จแล้ว เหลือ merge เข้า `main`) จึงทำแทนเป็นกรณีพิเศษครั้งเดียว และบันทึกไว้ตามข้อ 5 — งาน commit หลัก (`cab5583`) ผู้ใช้ยังทำเองใน GitHub Desktop |
