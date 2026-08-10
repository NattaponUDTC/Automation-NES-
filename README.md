# Automation NES — NES Reel Preview Generator

สร้างวิดีโอพรีวิว 15 วินาที (แนวตั้ง 1080x1920 สำหรับ Reels/Shorts) จาก NES ROM ทุกไฟล์โดยอัตโนมัติ โดยไม่ต้องเล่นเองทีละเกม

## วิธีทำงาน

1. `scripts/generic_preview.lua` — รันใน BizHawk, สุ่มกดปุ่ม (bias เดินหน้า/กระโดด) เป็นเวลา 900 เฟรม (15 วิ @ 60fps) แล้ว capture screenshot ทุกเฟรมลงโฟลเดอร์ที่กำหนด
2. `scripts/batch_generate.py` — วนลูปทุกไฟล์ `.nes` ใน `roms/`, สั่ง BizHawk รัน lua script ข้างต้นทีละเกม (headless ผ่าน `xvfb-run` ถ้าไม่มีจอ), จากนั้นใช้ ffmpeg ประกอบ screenshot ที่ได้เป็นวิดีโอ, scale/pad เป็นแนวตั้ง 1080x1920 (nearest-neighbor เพื่อรักษาความคมของ pixel art)
3. ไฟล์ผลลัพธ์แต่ละเกมจะถูกเซฟที่ `output/{ชื่อเกม}_reel.mp4`

รองรับทั้ง Windows (`EmuHawk.exe`) และ Linux (`EmuHawkMono.sh` ผ่าน mono)

## Setup — Linux (แนะนำ)

1. ดาวน์โหลด BizHawk build สำหรับ Linux จาก [official releases](https://github.com/TASEmulators/BizHawk/releases) (เช่น `BizHawk-2.11.1-linux-x64.tar.gz`) มาวางไว้ที่ root ของโปรเจกต์นี้
2. รัน:

   ```bash
   ./scripts/setup.sh
   ```

   สคริปต์นี้จะ:
   - ติดตั้ง dependencies ที่ BizHawk ต้องใช้บน Linux ผ่าน `apt` — `mono-complete`, `libopenal1`, `lsb-release` (ตามที่ระบุใน [README ของ BizHawk เอง](https://github.com/TASEmulators/BizHawk)) รวมถึง `ffmpeg` และ `xvfb` สำหรับรันแบบไม่มีจอ
   - แตก tarball ที่วางไว้ลง `./bizhawk/` และตั้ง execute permission ให้ `EmuHawkMono.sh`
   - สร้างโฟลเดอร์ `roms/` และ `output/` ให้พร้อมใช้

   > ถ้า `mono-complete` หาไม่เจอใน apt ของ distro คุณ ให้เพิ่ม [Mono official apt repo](https://www.mono-project.com/download/stable/#download-lin) ก่อนแล้วรันใหม่

3. วาง ROM ไฟล์ `.nes` ทั้งหมดที่ต้องการไว้ในโฟลเดอร์ `roms/`
4. ตรวจสอบว่าทุกอย่างพร้อม:

   ```bash
   python3 scripts/doctor.py
   ```

   ควรเห็น `[OK]` ทุกบรรทัด (ยกเว้น `[WARN]` เรื่องยังไม่มี ROM ถ้ายังไม่ได้วางไฟล์)

5. รัน:

   ```bash
   python3 scripts/batch_generate.py
   ```

## Setup — Windows

1. ดาวน์โหลดและแตก [BizHawk](https://tasvideos.org/BizHawk) ไว้ที่เครื่อง (เช่น `C:\BizHawk\EmuHawk.exe`)
2. ติดตั้ง [ffmpeg](https://ffmpeg.org/) แล้วเพิ่มเข้า `PATH` (ตรวจสอบด้วย `ffmpeg -version`)
3. ติดตั้ง Python 3.8+
4. แก้ `scripts/config.json` ให้ `bizhawk_path` ชี้ไปที่ `EmuHawk.exe` เช่น `"C:\\BizHawk\\EmuHawk.exe"`
5. วาง ROM ไว้ใน `roms/` แล้วรัน `python scripts\batch_generate.py`

## config.json

```json
{
  "bizhawk_path": "./bizhawk/EmuHawkMono.sh",
  "rom_dir": "./roms",
  "output_dir": "./output",
  "frames_dir": "./output/.frames",
  "timeout_sec": 60,
  "use_xvfb": "auto"
}
```

- `bizhawk_path` — path ไปยัง `EmuHawkMono.sh` (Linux) หรือ `EmuHawk.exe` (Windows); เป็น relative ต่อ root โปรเจกต์นี้ได้ (เช่น `./bizhawk/...`)
- `rom_dir` / `output_dir` / `frames_dir` — relative ต่อ root โปรเจกต์นี้ได้เช่นกัน
- `timeout_sec` — เวลาสูงสุดต่อเกม ก่อนจะ kill process แล้วข้ามไปเกมถัดไป
- `use_xvfb` — `"auto"` (ใช้ `xvfb-run` เฉพาะตอนไม่มี `$DISPLAY`, เหมาะกับรันบน server/CI), `"true"`/`"false"` เพื่อบังคับ

## Run

```bash
python3 scripts/batch_generate.py
```

- ก่อนเริ่ม จะตรวจสอบ (preflight) ว่ามี BizHawk, ffmpeg, mono, xvfb-run (ถ้าจำเป็น) ครบ ถ้าไม่ครบจะแจ้ง error ชัดเจนแล้วหยุดทันที ไม่ปล่อยให้พังกลางทาง
- ประมวลผลทุก ROM ใน `roms/` อัตโนมัติทีละไฟล์, ข้ามไฟล์ที่มี output อยู่แล้ว (resume ได้)
- log การทำงานอยู่ที่ `output/batch_log.txt`
- ถ้าเกมค้าง/ไม่ตอบสนอง จะถูก timeout และข้ามไปเกมถัดไปโดยอัตโนมัติ

## หมายเหตุ

- `generic_preview.lua` ใช้การสุ่ม input แบบมี bias (เดินหน้าเป็นหลัก, บางครั้งกระโดด/attack) เพื่อให้ดูเหมือนมีคนเล่นจริง และจะพยายามกด Start/A ในช่วงแรกเพื่อผ่าน title screen
- เหมาะกับ ROM ส่วนใหญ่ที่เป็นเกม platformer/action ที่เดินหน้าได้ อาจไม่เหมาะกับเกมแนว puzzle/menu-heavy
- โฟลเดอร์ screenshot ระหว่างประมวลผล (`frames_dir`) ถูกสร้าง/เคลียร์โดย `batch_generate.py` ก่อนรันทุกครั้ง แล้วส่ง path ให้ `generic_preview.lua` ผ่าน environment variable `NES_FRAMES_DIR` (มี fallback เป็นไฟล์ `scripts/.frames_dir` เผื่อ BizHawk build บาง build บล็อค `os.getenv`) — ไม่ได้พึ่งการ `mkdir` แบบ relative path จากฝั่ง Lua เพราะ working directory ของ BizHawk คือโฟลเดอร์ติดตั้งของมันเอง ไม่ใช่โฟลเดอร์โปรเจกต์นี้
- BizHawk build ที่ทดสอบ config นี้ด้วย: `BizHawk-2.11.1-linux-x64`

## Troubleshooting

รัน `python3 scripts/doctor.py` ก่อนเสมอเมื่อเจอปัญหา — จะบอกตรงๆ ว่าอะไรขาด (ffmpeg, BizHawk, mono, xvfb-run, permission, ROM) และวิธีแก้
