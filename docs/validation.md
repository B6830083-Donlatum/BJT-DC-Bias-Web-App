# Validation — BJT DC Bias Web App (Lab 02)

วันที่: 2026-11-10
อ้างอิง: `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md` §10

## 1. ค่าอ้างอิง (Reference Operating Point)

พารามิเตอร์ที่ใช้ตรวจ: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

### 1.1 คำนวณมือ (Forward-Active)

```
VTH = 12 · 22 / (100 + 22)          = 2.163934 V
RTH = 100 · 22 / (100 + 22) kΩ      = 18.032787 kΩ
IB  = (2.163934 − 0.70) / (18.032787k + 101·1k)
    = 1.463934 / 119032.787         = 12.2986 µA
IC  = 100 · 12.2986 µA              = 1.229858 mA
IE  = 101 · 12.2986 µA              = 1.242157 mA
VE  = 1.242157 mA · 1 kΩ            = 1.242157 V
VB  = 1.242157 + 0.70               = 1.942157 V
VC  = 12 − 1.229858 mA · 2.2 kΩ     = 9.294312 V
VCE = 9.294312 − 1.242157           = 8.052155 V
```

### 1.2 ผลจากโปรแกรม

| ปริมาณ | ค่าที่คำนวณมือ | ค่าจากโปรแกรม | ผลต่าง | ผลตรวจ |
|--------|----------------|----------------|--------|---------|
| VTH | 2.163934 V | 2.163934 V | < 1e-6 | ✅ |
| RTH | 18.032787 kΩ | 18.032787 kΩ | < 1e-6 | ✅ |
| IB | 12.2986 µA | 12.2986 µA | < 1e-9 A | ✅ |
| IC | 1.229858 mA | 1.229858 mA | < 1e-9 A | ✅ |
| IE | 1.242157 mA | 1.242157 mA | < 1e-9 A | ✅ |
| VE | 1.242157 V | 1.242157 V | < 1e-6 | ✅ |
| VB | 1.942157 V | 1.942157 V | < 1e-6 | ✅ |
| VC | 9.294312 V | 9.294312 V | < 1e-6 | ✅ |
| VCE | 8.052155 V | 8.052155 V | < 1e-6 | ✅ |
| Region | active | active | – | ✅ |

**Tolerance ที่ใช้ในเทสต์**

- แรงดัน: `places=3` (±0.0005 V) และ `delta=1.0 Ω` สำหรับ RTH
- กระแส: `delta=1e-8 A` (IB) และ `delta=1e-7 A` (IC, IE)
- ตัวเลขที่แสดงบนหน้าเว็บปัดเป็นทศนิยม 3 ตำแหน่ง → `VCE = 8.052 V`, `IC = 1.230 mA`

### 1.3 ผลจากหน้าเว็บจริง (HTTP)

```
POST http://127.0.0.1:5000/calculate
→ 200 OK
<span class="badge active">ACTIVE</span>
<div class="result"><span>VCE</span><strong>8.052 V</strong></div>
<div class="result"><span>IC</span><strong>1.230 mA</strong></div>
```

## 2. ผลทดสอบกรณีไม่ถูกต้อง (Validation)

| อินพุต | ผลที่คาดหวัง | ผลจริง |
|--------|--------------|--------|
| `R1 = 0` | HTTP 400 + error "R1 ต้องเป็นค่ามากกว่าศูนย์" | ✅ |
| `β = 0` | HTTP 400 + error "β ต้องเป็นค่ามากกว่าศูนย์" | ✅ |
| `VCC = −1` | HTTP 400 + error "VCC ต้องเป็นค่ามากกว่าศูนย์" | ✅ |
| `R1 = "abc"` | HTTP 400 + error "R1 ต้องเป็นตัวเลข" (ไม่ raise exception) | ✅ |
| `R1 = "1,000"` | HTTP 400 + error "R1 ต้องเป็นตัวเลข" | ✅ |
| ฟอร์มส่งมาแค่ `vcc` | HTTP 400 + error ครบทุก field ที่ขาด (ไม่ `KeyError`/500) | ✅ |
| `R1 = " 100 "` (มีช่องว่าง) | ผ่าน และได้ 100 kΩ | ✅ |
| `R1 = "nan"` / `"inf"` | HTTP 400 + error "R1 ต้องเป็นจำนวนจำกัด" | ✅ |

## 3. ผลทดสอบ Operating Region

### 3.1 Cutoff — R2 เล็กมาก (VTH ≤ VBE)

พารามิเตอร์: VCC = 12 V, R1 = 100 kΩ, R2 = 1 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

| ปริมาณ | ค่า |
|--------|-----|
| VTH | 0.118812 V (≤ VBE) |
| IB, IC, IE | 0 A |
| VB | 0.118812 V (= VTH เพราะไม่มีกระแสเบส) |
| VE | 0 V |
| VC | 12.000 V |
| VCE | 12.000 V |
| Region | `cutoff` |
| Warning | "วงจรอยู่ในช่วง Cutoff — แบบจำลอง Forward-Active ใช้ไม่ได้" |

> ในช่วง Cutoff ไม่มีกระแสเบสไหล แรงดันที่เบสจึงเท่ากับ VTH (0.119 V) ไม่ใช่ VE + VBE (0.70 V)
> เพราะสมการ `VB = VE + VBE` ใช้ได้เฉพาะ Forward Active

### 3.2 Saturation — RC ใหญ่จน VCE < 0.3 V

พารามิเตอร์: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 10 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

| ปริมาณ | ค่า |
|--------|-----|
| IC | 1.229858 mA |
| VC | −0.298581 V |
| VCE | −1.540738 V (< 0.3 V) |
| Region | `saturation` |
| Warning | "VCE ต่ำกว่า 0.3 V — อาจอยู่ในช่วง Saturation ผลจากแบบจำลอง Forward-Active ไม่น่าเชื่อถือ" |

> หมายเหตุ: `VC` ติดลบเพราะแบบจำลอง Forward-Active ยังคงใช้สมการเดิม ทั้งที่ของจริง transistor
> จะอิ่มตัว (saturate) — นี่คือเหตุผลที่ต้องมี warning ไม่ใช่ปล่อยให้อ่านค่าตรง ๆ

## 4. ผลทดสอบกรณี β ต่ำมาก (β = 1)

| ปริมาณ | ค่า | ตรวจ |
|--------|-----|------|
| IB | 73.0769 µA | finite ✅ |
| IC | 73.0769 µA | finite ✅ |
| IE | 146.1538 µA | finite ✅ |
| VCE | 11.693077 V | finite ✅ |

ไม่เกิดการหารศูนย์ และไม่มีค่า NaN/inf

## 5. ผลรัน Automated Tests

```
python -m unittest discover -s tests -v
```

- `tests/test_dc_bias.py` — 13 tests (reference values, unit conversion, parsing, validation, region detection, β = 1, non-finite input)
- `tests/test_web.py` — 3 tests (GET /, POST valid, POST invalid)
- **รวม 16 tests — PASS ทั้งหมด**

## 6. ตรวจว่าไม่มีตัวเลข hardcode ใน template

```
Select-String -Path templates\index.html -Pattern "8\.05|1\.23"
```

→ ไม่พบผลลัพธ์ (ทุกค่ามาจาก `result.*` ผ่าน Jinja2)

## 7. ข้อจำกัดที่ยังเหลือ

- ตัวเลขบนหน้าเว็บปัด 3 ตำแหน่ง อาจต่างจากเครื่องคิดเลขที่ปัดต่างกันในหลักสุดท้าย
- แบบจำลองไม่คิด Early effect/อุณหภูมิ จึงใช้ยืนยัน "แนวโน้ม" และ "operating point โดยประมาณ" เท่านั้น
- ค่า Saturation ที่ได้เป็นผลจากสมการ Forward-Active ไม่ใช่คำตอบจริงของวงจรอิ่มตัว
