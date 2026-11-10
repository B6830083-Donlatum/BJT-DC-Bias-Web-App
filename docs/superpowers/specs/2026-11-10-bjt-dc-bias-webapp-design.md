# Design — BJT DC Bias Web App (Lab 02)

วันที่: 2026-11-10
รายวิชา: ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
ผู้จัดทำ: นักศึกษา (B6830083) + OpenCode/Superpowers
สถานะ: รออนุมัติ Design

## 1. Intent (ทำไมทำ)

ส่งงาน Lab 02 ด้วย Flask Web Application ที่ **คำนวณ DC Operating Point จริงด้วย Python Backend**
ไม่ใช่ HTML ที่ฝังตัวเลขไว้ และต้องผ่านเกณฑ์ตรวจรับ A1–A7 ภายในคาบเดียว

## 2. Goals (เกณฑ์ตรวจรับ)

| ID | เป้าหมาย |
|----|----------|
| A1 | `GET /` → HTTP 200 + เห็นฟอร์มกรอกค่า |
| A2 | `POST /calculate` → Python คำนวณ แล้ว render ผลใน HTML (ไม่ hardcode) |
| A3 | ค่าตรงกับการคำนวณอิสระภายใต้ Forward-Active model |
| A4 | R≤0, β≤0, ค่าที่ไม่ใช่ตัวเลข → error ที่อ่านรู้เรื่อง หน้าเว็บไม่ล้ม |
| A5 | นอก Active Region (cutoff / saturation) → warning ชัดเจน |
| A6 | ≥3 automated tests ฝั่ง engineering + ≥1 test ผ่าน Flask test client |
| A7 | clone repo → ติดตั้ง → รันเว็บ → รัน tests ได้ตาม README |

## 3. Non-goals / Anti-goals

- ไม่ทำ AC small-signal, Bode plot, transient, signal generator, SPICE/ngspice
- ไม่ทำ bias แบบอื่น (Fixed, Emitter) — อยู่ใน W3
- ไม่มี auth, database, deployment, Docker
- **Anti-goal:** แสดงตัวเลขผลลัพธ์ที่ hardcode ใน template หรือคำนวณด้วย JavaScript ฝั่ง client

## 4. Constraints

- Python 3.15.2, Flask 3.1.3 (ทดสอบติดตั้งแล้ว)
- Windows 11, path คั่นด้วย `\`
- Commit/Push ทำผ่าน **GitHub Desktop** (ไม่ใช้ git CLI commit)
- Timebox: ต้องจบในคาบ (Build ~75 นาที)

## 5. Approaches ที่พิจารณา

| ทาง | ข้อดี | ข้อเสีย | สรุป |
|-----|-------|---------|------|
| **1. Multi-file Flask ตามโครงเอกสาร** | ตรงเกณฑ์ A2/A6, แยกสมการออกจาก HTTP, ต่อยอด W3 ง่าย | ไฟล์หลายไฟล์ | **เลือก** |
| 2. App factory + Blueprint | รองรับหลาย bias type ใน W3 ได้สวยกว่า | เพิ่ม indirection โดยไม่ได้คะแนนเพิ่มในคาบนี้ | ไม่เลือก (refactor ทีหลังได้ถูก) |
| 3. Single-file Flask หรือคำนวณด้วย JS | เขียนเร็ว | ผิดเกณฑ์ A2 (ต้องเป็น Python backend) และ A6 | ตัดทิ้ง |

## 6. โครงสร้างไฟล์

```
app.py                  Flask routes (GET /, POST /calculate)
dc_bias.py              สมการ + validation (ไม่รู้จัก HTML/HTTP)
templates/index.html    ฟอร์ม + ผลลัพธ์ (Jinja2)
static/style.css        responsive layout
tests/test_dc_bias.py   unit tests ฝั่ง engineering
tests/test_web.py       Flask test client
requirements.txt        Flask==3.1.3
README.md               วิธีติดตั้ง/รัน/ทดสอบ
AGENTS.md               convention สำหรับ AI agent
.gitignore              .venv/, __pycache__/, *.pyc, .env
docs/design-note.md     บันทึกการออกแบบ
docs/validation.md      ผลตรวจสอบกับค่าอ้างอิง
docs/reflection.md      สิ่งที่ได้เรียนรู้
```

## 7. โมเดลวิศวกรรม (dc_bias.py)

ฟังก์ชันบริสุทธิ์ (pure functions) ไม่แตะ HTTP:

- `validate_inputs(raw: dict) -> tuple[BiasInputs | None, list[str]]`
- `calculate_dc_bias(inputs: BiasInputs) -> BiasResult`

สมการ (Forward-Active, β คงที่, VBE คงที่):

```
VTH = VCC · R2 / (R1 + R2)
RTH = R1 · R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β · IB
IE  = (β+1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

**หน่วยภายใน:** V, Ω, A ทั้งหมด (แปลง kΩ → Ω ที่ชั้น validation)

**การตัดสิน Region:**

| เงื่อนไข | Region | การกระทำ |
|----------|--------|----------|
| `VTH ≤ VBE` (IB ≤ 0) | Cutoff | IC=0, VCE=VCC + warning ว่า model Forward-Active ใช้ไม่ได้ |
| `VCE < 0.3 V` | Saturation (ใกล้/เข้า) | แสดงค่าตามสมการ + warning |
| อื่น ๆ | Forward Active | แสดงผลปกติ |

## 8. UI / การรับค่า

- ฟอร์ม: `VCC [V]`, `R1`, `R2`, `RC`, `RE` (แต่ละช่องมี dropdown หน่วย Ω/kΩ, **default kΩ**), `β`, `VBE [V]`
- ค่าเริ่มต้นในฟอร์ม: 12 V, 100 kΩ, 22 kΩ, 2.2 kΩ, 1 kΩ, β=100, VBE=0.70 V
- ผลลัพธ์: การ์ดสรุป `VB, VE, VC, VCE [V]` และ `IC [mA]` + ตารางรอง `IB, IE, VTH, RTH`
- แสดง **badge Operating Region** (Active / Cutoff / Saturation)
- Error/Warning แสดงเป็นกล่องสี ไม่ทำให้หน้าเว็บล้ม
- ภาษาบนหน้าจอ: ไทยเป็นหลัก + ศัพท์เทคนิคอังกฤษ
- Responsive 1 คอลัมน์บนมือถือ, 2 คอลัมน์บนเดสก์ท็อป

## 9. HTTP Contract

| Route | Method | Input | Output |
|-------|--------|-------|--------|
| `/` | GET | – | 200 + ฟอร์ม (ค่า default) |
| `/calculate` | POST | form fields | 200 + ผลลัพธ์ / **400** + ฟอร์มพร้อม error |

- Validation ฝั่ง server เท่านั้นเป็นแหล่งความจริง (HTML `required` เป็นแค่ UX)
- ไม่ใช้ session, ไม่มี state ฝั่ง server

## 10. Testing Strategy

`tests/test_dc_bias.py`
1. ค่าอ้างอิง VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.7 → VB≈1.942, VE≈1.242, VC≈9.294, VCE≈8.052, IC≈1.230 mA (tolerance 1e-3)
2. การแปลงหน่วย kΩ → Ω ให้ผลเท่ากับการกรอกเป็น Ω
3. Invalid: R=0, β=0, non-numeric → ได้ error list, ไม่ raise exception
4. Cutoff: R2 เล็กมาก (VTH ≤ VBE) → region=cutoff + warning
5. Saturation: RC ใหญ่/RE เล็ก จน VCE < 0.3 V → warning

`tests/test_web.py`
1. `GET /` → 200 และมี `name="vcc"`
2. `POST /calculate` ค่าถูกต้อง → 200 และมี `8.05` หรือ `VCE`
3. `POST /calculate` ค่า invalid → 400 และมีข้อความ error

## 11. ความเสี่ยง

| ความเสี่ยง | การรับมือ |
|------------|-----------|
| Python 3.15 ใหม่มาก | ทดสอบ Flask 3.1.3 แล้วว่าใช้ได้ |
| ตัวเลขปัดเศษไม่ตรงกับที่อาจารย์คำนวณ | ระบุ tolerance และแสดงทศนิยม 3 ตำแหน่ง + บันทึกใน validation.md |
| ผู้ใช้กรอก kΩ แต่ลืมเปลี่ยนหน่วย | default เป็น kΩ ตามค่าตัวอย่าง และ echo หน่วยกลับในผลลัพธ์ |

## 12. สิ่งที่ยังเปิดอยู่ (ให้ builder ตัดสิน)

- โทนสี/ฟอนต์ของ UI (ใช้ CSS variables, โทนน้ำเงิน-เทาตามเอกสาร)
- จะแยก `_results.html` หรือใช้ `{% if %}` ในไฟล์เดียว → เลือกไฟล์เดียวเพื่อลดจำนวนไฟล์
