# AGENTS.md — กติกาสำหรับ AI agent ในโปรเจกต์นี้

## ขอบเขต

โปรเจกต์นี้เป็นงาน Lab 02 ของ ENG29 2121: Flask Web App คำนวณ DC Bias ของ
BJT Common-Emitter (Voltage-Divider Bias) เท่านั้น

**ห้ามเพิ่ม** AC analysis, Bode plot, transient, signal generator, SPICE,
bias แบบอื่น หรือระบบ login/database โดยไม่ได้รับอนุญาตจากผู้ใช้

## กติกาการเขียนโค้ด

1. สมการฟิสิกส์ทั้งหมดอยู่ใน `dc_bias.py` เท่านั้น
   - `app.py` ทำหน้าที่รับ HTTP request, เรียกฟังก์ชัน, render template
   - `templates/index.html` ห้ามมีสมการและ **ห้าม hardcode ตัวเลขผลลัพธ์**
2. หน่วยภายในโมดูลเป็น SI (V, Ω, A) การแปลง kΩ → Ω ทำที่ `parse_form()` เท่านั้น
3. ฟังก์ชันใน `dc_bias.py` ต้องเป็น pure function ไม่มี side effect
4. ข้อความ error/warning ที่ผู้ใช้เห็นเป็นภาษาไทย ระบุชื่อพารามิเตอร์ให้ชัด

## กติกากระบวนการ

1. เขียน test ก่อนแก้โค้ดทุกครั้ง (TDD) และต้องเห็น test fail ก่อน implement
2. รัน `python -m unittest discover -s tests -v` ให้เขียวก่อนอ้างว่างานเสร็จ
3. **ห้ามรัน `git commit` หรือ `git push`** — ผู้ใช้ commit ผ่าน GitHub Desktop เท่านั้น
4. อย่าลบหรือแก้ไฟล์ใน `docs/superpowers/` โดยไม่แจ้งผู้ใช้
5. ถ้าต้องตัดสินใจแทนผู้ใช้ ให้บันทึกเหตุผลไว้ใน `docs/design-note.md`
