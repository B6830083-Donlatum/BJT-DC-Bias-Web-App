# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจรขยาย BJT
Common-Emitter แบบ **Voltage-Divider Bias** (Forward-Active approximation)

- ENG29 2121 Computer Programming for Electrical Engineers (2/2569)
- Lab 02 — OpenCode + Superpowers

## ต้องมีอะไรก่อน

- Python 3.10 ขึ้นไป (ทดสอบบน 3.15.2)
- Git (เฉพาะกรณี clone repository)

## ติดตั้ง

```powershell
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

python -m pip install -r requirements.txt
```

## รันเว็บ

```powershell
python -m flask --app app run --debug
```

เปิดเบราว์เซอร์ที่ **http://127.0.0.1:5000/**

> ต้องเปิดผ่าน Flask server เท่านั้น การ double-click เปิด `templates/index.html`
> จะไม่ทำงาน เพราะการคำนวณอยู่ที่ Python backend

## รันเทสต์

```powershell
python -m unittest discover -s tests -v
```

## ค่าเริ่มต้นที่ใช้ตรวจสอบ

| พารามิเตอร์ | ค่า |
|---|---|
| VCC | 12 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RC | 2.2 kΩ |
| RE | 1 kΩ |
| β | 100 |
| VBE | 0.70 V |

ผลที่ควรได้: VB ≈ 1.942 V, VE ≈ 1.242 V, VC ≈ 9.294 V, VCE ≈ 8.052 V, IC ≈ 1.230 mA

## สมมติฐานและข้อจำกัด

- ใช้ **Forward-Active approximation**: β คงที่ และ VBE คงที่
- ไม่ใช่ SPICE/ngspice — ไม่คิด Early effect, temperature, ความคลาดเคลื่อนของอุปกรณ์
- ถ้า `VTH ≤ VBE` วงจรจะอยู่ในช่วง **Cutoff** และแบบจำลองนี้ใช้ไม่ได้
- ถ้า `VCE < 0.3 V` ให้ถือว่าใกล้/เข้า **Saturation** และผลจากแบบจำลองไม่น่าเชื่อถือ
- ผลลัพธ์ที่อยู่นอก Forward Active ต้องอ่านพร้อม warning เสมอ

## โครงสร้างโปรเจกต์

```
app.py                  Flask routes (HTTP เท่านั้น)
dc_bias.py              สมการ + validation (ไม่รู้จัก HTML/HTTP)
templates/index.html    ฟอร์ม + ผลลัพธ์ (Jinja2)
static/style.css        หน้าตาเว็บ
tests/                  unittest (engineering + Flask client)
docs/                   design note, validation, reflection
```
