# Automation NES — NES Reel Preview Generator

สร้างวิดีโอพรีวิว 15 วินาที (แนวตั้ง 1080x1920 สำหรับ Reels/Shorts) จาก NES ROM ทุกไฟล์โดยอัตโนมัติ โดยไม่ต้องเล่นเองทีละเกม

## วิธีทำงาน

1. `scripts/generic_preview.lua` — รันใน BizHawk, สุ่มกดปุ่ม (bias เดินหน้า/กระโดด) เป็นเวลา 900 เฟรม (15 วิ @ 60fps) แล้ว capture screenshot ทุกเฟรมลงโฟลเดอร์ที่กำหนด
2. `scripts/batch_generate.py` — วนลูปทุกไฟล์ `.nes` ใน `roms/`, สั่ง BizHawk รัน lua script ข้างต้นทีละเกม (ถ้าไม่มีจอจริงจะครอบด้วย `xvfb-run` ให้อัตโนมัติ — ดูความเสี่ยงเรื่องนี้ในหัวข้อ "ไม่มีจอจริง" ด้านล่าง), จากนั้นใช้ ffmpeg ประกอบ screenshot ที่ได้เป็นวิดีโอ, scale/pad เป็นแนวตั้ง 1080x1920 (nearest-neighbor เพื่อรักษาความคมของ pixel art)
3. ไฟล์ผลลัพธ์แต่ละเกมจะถูกเซฟที่ `output/{ชื่อเกม}_reel.mp4`

รองรับทั้ง Windows (`EmuHawk.exe`) และ Linux (`EmuHawkMono.sh` ผ่าน mono)

## Setup — Linux (แนะนำ)

1. ดาวน์โหลด BizHawk build สำหรับ Linux จาก [official releases](https://github.com/TASEmulators/BizHawk/releases) (เช่น `BizHawk-2.11.1-linux-x64.tar.gz`) มาวางไว้ที่ root ของโปรเจกต์นี้
2. วาง ROM ไฟล์ `.nes` ที่ต้องการไว้ในโฟลเดอร์ `roms/`
3. รันคำสั่งเดียว:

   ```bash
   ./scripts/report.sh
   ```

   สคริปต์นี้ทำให้ครบในรันเดียว: ติดตั้ง dependency ที่ BizHawk ต้องใช้ (`mono-complete`, `libopenal1`, `lsb-release` ตาม [README ของ BizHawk เอง](https://github.com/TASEmulators/BizHawk) รวมถึง `ffmpeg`/`xvfb`), แตก tarball ลง `./bizhawk/` (ข้ามอัตโนมัติถ้าแตกไว้แล้ว), เช็ค environment (`doctor.py`), แล้วทดสอบรันจริง 1 ROM (`smoke_test.py`) — จบแล้วสรุปสถานะ **READY**/**NOT READY** ให้ พร้อมเซฟรายงานเป็นไฟล์ `report_<เวลา>.txt` ไว้ด้วย

   > **ก๊อปข้อความที่ terminal พิมพ์ออกมาทั้งหมดส่งกลับมาได้เลย** ถ้าสถานะเป็น NOT READY หรือมีอะไรดูแปลกๆ — จะได้ดูแล้วบอกวิธีแก้ได้ตรงจุด ไม่ต้องรันสคริปต์ทีละตัวเอง
   >
   > ถ้า `mono-complete` หาไม่เจอใน apt ของ distro คุณ ให้เพิ่ม [Mono official apt repo](https://www.mono-project.com/download/stable/#download-lin) ก่อนแล้วรันใหม่

4. ถ้าสถานะเป็น **READY** รันจริงทั้งหมด:

   ```bash
   python3 scripts/batch_generate.py
   ```

   (จะรันเฉพาะเมื่ออยากได้ผลลัพธ์จริงเท่านั้น — ขั้นตอนนี้อาจใช้เวลานานเป็นชั่วโมงถ้ามี ROM เยอะ ไม่ต้องรันซ้ำผ่าน `report.sh`)

### รันแยกทีละตัวเอง (ถ้าไม่อยากใช้ report.sh)

```bash
./scripts/setup.sh        # ติดตั้ง dependency + แตก BizHawk tarball
python3 scripts/doctor.py    # เช็ค environment
python3 scripts/smoke_test.py  # ทดสอบเร็ว 1 ROM
python3 scripts/batch_generate.py  # รันจริงทั้งหมด
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

รัน `./scripts/report.sh` ก่อนเสมอ (ดูขั้นตอนใน Setup ด้านบน) จนกว่าจะเห็นสถานะ **READY** — มันรวม `smoke_test.py` (ทดสอบ ROM เดียว ~30 เฟรม ไม่กี่วินาที) ไว้ให้แล้ว สำคัญเป็นพิเศษถ้าเครื่องไม่มีจอจริง (ดูหัวข้อ "ไม่มีจอ" ด้านล่าง)

พอ READY แล้วค่อยรันจริงทั้งหมด:

```bash
python3 scripts/batch_generate.py
```

- ก่อนเริ่ม จะตรวจสอบ (preflight) ว่ามี BizHawk, ffmpeg, mono, xvfb-run (ถ้าจำเป็น) ครบ ถ้าไม่ครบจะแจ้ง error ชัดเจนแล้วหยุดทันที ไม่ปล่อยให้พังกลางทาง
- ประมวลผลทุก ROM ใน `roms/` อัตโนมัติทีละไฟล์, ข้ามไฟล์ที่มี output อยู่แล้ว (resume ได้)
- log การทำงานอยู่ที่ `output/batch_log.txt`
- ถ้าเกมค้าง/ไม่ตอบสนอง จะถูก timeout และข้ามไปเกมถัดไปโดยอัตโนมัติ

## ไม่มีจอจริง (headless server) — ใช้ได้จริงไหม?

**ตอบตรงๆ: มีความเสี่ยงที่ยังไม่เคยมีใครยืนยันว่าใช้ได้ 100% กับ BizHawk**

- BizHawk **ไม่มี** headless mode อย่างเป็นทางการ — ทีมพัฒนายืนยันเองว่า priority ต่ำมาก ไม่มีแผนทำ ([อ้างอิง](https://tasvideos.org/Forum/Topics/20293))
- โปรเจกต์นี้แก้ปัญหาด้วย `xvfb-run` (สร้างจอเสมือนใน memory) ซึ่งเป็นเทคนิคมาตรฐานสำหรับรันแอพ GUI บน Linux server (ใช้กับ CI/browser automation ทั่วไป) — `use_xvfb: "auto"` ใน config จะเปิดใช้เองถ้าไม่มี `$DISPLAY`
- เพื่อลดความเสี่ยงเรื่อง OpenGL context (ปัญหาที่พบบ่อยที่สุดเวลาบังคับแอพ GUI ให้รันผ่านจอเสมือน) โปรเจกต์นี้ตั้ง `LIBGL_ALWAYS_SOFTWARE=1` ให้อัตโนมัติ และใช้จอเสมือนขนาด 1280x1024x24 (ไม่ใช่ค่า default เล็กๆ ของ `xvfb-run`)
- แต่**ไม่มีแหล่งไหนยืนยันว่ามีคนรัน BizHawk สำเร็จผ่าน Xvfb มาก่อน** — จึงต้องรัน `./scripts/report.sh` ก่อนเสมอเพื่อเช็คจริงบนเครื่องของคุณ (มี smoke test อยู่ในนั้น) ถ้าสถานะออกมาเป็น NOT READY ก๊อปรายงานทั้งหมดที่มันพิมพ์ส่งกลับมาได้เลย จะดูให้ว่าปัญหาคืออะไร (มักเป็นปัญหา GL/GLX)

**ถ้า smoke test fail บนเครื่องไม่มีจอจริง** ทางเลือกสำรอง:
1. รันบนเครื่องที่มี desktop environment จริง หรือต่อผ่าน VNC/RDP (ตั้ง `$DISPLAY` เอง ระบบจะข้าม `xvfb-run` อัตโนมัติเพราะ `use_xvfb: "auto"`)
2. รันในคอนเทนเนอร์ desktop แบบเบา (เช่น Distrobox/Docker ที่มี X server ข้างในเต็มรูปแบบ ไม่ใช่แค่ Xvfb) — ดูตัวอย่างแนวทางนี้ใน [Steam Deck BizHawk setup guide](https://gist.github.com/SpenserHaddad/417a772aea5be99d563fe73295bb62fb) (ใช้ Distrobox)
3. ลองปรับ `xvfb-run` args เองใน `scripts/batch_generate.py` (`build_command()`) ตาม error ที่เจอ

## หมายเหตุ

- `generic_preview.lua` ใช้การสุ่ม input แบบมี bias (เดินหน้าเป็นหลัก, บางครั้งกระโดด/attack) เพื่อให้ดูเหมือนมีคนเล่นจริง และจะพยายามกด Start/A ในช่วงแรกเพื่อผ่าน title screen
- เหมาะกับ ROM ส่วนใหญ่ที่เป็นเกม platformer/action ที่เดินหน้าได้ อาจไม่เหมาะกับเกมแนว puzzle/menu-heavy
- โฟลเดอร์ screenshot ระหว่างประมวลผล (`frames_dir`) ถูกสร้าง/เคลียร์โดย `batch_generate.py` ก่อนรันทุกครั้ง แล้วส่ง path ให้ `generic_preview.lua` ผ่าน environment variable `NES_FRAMES_DIR` (มี fallback เป็นไฟล์ `scripts/.frames_dir` เผื่อ BizHawk build บาง build บล็อค `os.getenv`) — ไม่ได้พึ่งการ `mkdir` แบบ relative path จากฝั่ง Lua เพราะ working directory ของ BizHawk คือโฟลเดอร์ติดตั้งของมันเอง ไม่ใช่โฟลเดอร์โปรเจกต์นี้
- BizHawk build ที่ทดสอบ config นี้ด้วย: `BizHawk-2.11.1-linux-x64`

## Troubleshooting

รัน `./scripts/report.sh` ก่อนเสมอเมื่อเจอปัญหา แล้วก๊อปข้อความทั้งหมดที่มันพิมพ์ (หรือเนื้อหาไฟล์ `report_*.txt` ที่มันเซฟไว้) ส่งกลับมาได้เลย — มันรวมข้อมูล system, tool versions, ROM, ผล `doctor.py`, และผล `smoke_test.py` ไว้ในที่เดียว ไม่ต้องรันหลายคำสั่งเอง
