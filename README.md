# Automation NES — NES Reel Preview Generator

สร้างวิดีโอพรีวิว 15 วินาที (แนวตั้ง 1080x1920 สำหรับ Reels/Shorts) จาก NES ROM ทุกไฟล์โดยอัตโนมัติ โดยไม่ต้องเล่นเองทีละเกม

## วิธีทำงาน

1. `scripts/generic_preview.lua` — รันใน BizHawk, สุ่มกดปุ่ม (bias เดินหน้า/กระโดด) เป็นเวลา 900 เฟรม (15 วิ @ 60fps) แล้ว capture screenshot ทุกเฟรมลงโฟลเดอร์ `frames/`
2. `scripts/batch_generate.py` — วนลูปทุกไฟล์ `.nes` ใน `roms/`, สั่ง BizHawk รัน lua script ข้างต้นแบบ headless ทีละเกม, จากนั้นใช้ ffmpeg ประกอบ screenshot ที่ได้เป็นวิดีโอ, scale/pad เป็นแนวตั้ง 1080x1920 (nearest-neighbor เพื่อรักษาความคมของ pixel art)
3. ไฟล์ผลลัพธ์แต่ละเกมจะถูกเซฟที่ `output/{ชื่อเกม}_reel.mp4`

## Prerequisites

- [BizHawk](https://tasvideos.org/BizHawk) (emulator, ใช้ `EmuHawk.exe`) — ไม่ commit ไว้ในโปรเจกต์นี้เพราะเป็นไฟล์ binary ขนาดใหญ่ ให้ดาวน์โหลดแยกต่างหาก
- [ffmpeg](https://ffmpeg.org/) อยู่ใน `PATH` (ตรวจสอบด้วย `ffmpeg -version`)
- Python 3.8+

## Setup

1. วาง ROM ไฟล์ `.nes` ทั้งหมดที่ต้องการไว้ในโฟลเดอร์ `roms/`
2. แก้ `scripts/config.json` ให้ตรงกับเครื่องของคุณ:

   ```json
   {
     "bizhawk_exe": "C:\\BizHawk\\EmuHawk.exe",
     "rom_dir": "C:\\nes-reel-project\\roms",
     "output_dir": "C:\\nes-reel-project\\output",
     "frames_dir": "C:\\BizHawk\\frames",
     "timeout_sec": 60
   }
   ```

   - `bizhawk_exe` — path ไปยัง `EmuHawk.exe`
   - `rom_dir` — path ไปยังโฟลเดอร์ที่เก็บไฟล์ `.nes`
   - `output_dir` — path ไปยังโฟลเดอร์ที่จะเซฟวิดีโอผลลัพธ์
   - `frames_dir` — path ที่ BizHawk จะ capture screenshot ระหว่างรัน lua script (ต้องตรงกับ path ที่ BizHawk มองเห็นโฟลเดอร์ `frames` ที่ lua script สร้าง)
   - `timeout_sec` — เวลาสูงสุดต่อเกม ก่อนจะ kill process แล้วข้ามไปเกมถัดไป

## Run

```bash
python scripts/batch_generate.py
```

- ประมวลผลทุก ROM ใน `roms/` อัตโนมัติทีละไฟล์, ข้ามไฟล์ที่มี output อยู่แล้ว (resume ได้)
- log การทำงานอยู่ที่ `output/batch_log.txt`
- ถ้าเกมค้าง/ไม่ตอบสนอง จะถูก timeout และข้ามไปเกมถัดไปโดยอัตโนมัติ

## หมายเหตุ

- `generic_preview.lua` ใช้การสุ่ม input แบบมี bias (เดินหน้าเป็นหลัก, บางครั้งกระโดด/attack) เพื่อให้ดูเหมือนมีคนเล่นจริง ไม่ใช่การเดินแบบสุ่มล้วน ๆ และจะพยายามกด Start/A ในช่วงแรกเพื่อผ่าน title screen
- เหมาะกับ ROM ส่วนใหญ่ที่เป็นเกม platformer/action ที่เดินหน้าได้ อาจไม่เหมาะกับเกมแนว puzzle/menu-heavy
- BizHawk build ที่ใช้ทดสอบ: `BizHawk-2.11.1-linux-x64` (ดาวน์โหลดจาก [ที่เก็บ release อย่างเป็นทางการ](https://github.com/TASEmulators/BizHawk/releases))
