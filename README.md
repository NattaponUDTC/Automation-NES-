# Automation NES — NES Reel Preview Generator

สร้างวิดีโอพรีวิว 15 วินาที (แนวตั้ง 1080x1920 สำหรับ Reels/Shorts) จาก NES ROM ทุกไฟล์โดยอัตโนมัติ โดยไม่ต้องเล่นเองทีละเกม

## วิธีทำงาน

1. `scripts/generic_preview.lua` — รันใน BizHawk, สุ่มกดปุ่ม (bias เดินหน้า/กระโดด) เป็นเวลา 900 เฟรม (15 วิ @ 60fps) แล้ว capture screenshot ทุกเฟรมลงโฟลเดอร์ที่กำหนด
2. `scripts/batch_generate.py` — วนลูปทุกไฟล์ `.nes` ใน `roms/`, สั่ง BizHawk รัน lua script ข้างต้นทีละเกม (ถ้าไม่มีจอจริงจะครอบด้วย `xvfb-run` ให้อัตโนมัติ — ดูความเสี่ยงเรื่องนี้ในหัวข้อ "ไม่มีจอจริง" ด้านล่าง), จากนั้นใช้ ffmpeg ประกอบ screenshot ที่ได้เป็นวิดีโอ, scale/pad เป็นแนวตั้ง 1080x1920 (nearest-neighbor เพื่อรักษาความคมของ pixel art)
3. ไฟล์ผลลัพธ์แต่ละเกมจะถูกเซฟที่ `output/{ชื่อเกม}_reel.mp4`

รองรับทั้ง Windows (`EmuHawk.exe`) และ Linux (`EmuHawkMono.sh` ผ่าน mono)

## Setup — Linux (แนะนำ)

> ⚠️ **สำคัญ: ห้ามรัน `smoke_test.py`/`batch_generate.py`/`report.sh` ด้วย user `root`** (ทดสอบยืนยันแล้วว่าค้างตลอดไปแบบไม่มี error) — `setup.sh` เองรันเป็น root/sudo ได้ปกติ (ใช้แค่ติดตั้ง package) แต่ขั้นตอนที่เหลือต้องรันเป็น user ธรรมดา ถ้ายังไม่มี user ธรรมดาบนเครื่อง สร้างก่อน:
> ```bash
> sudo useradd -m nesuser && sudo chown -R nesuser:nesuser /path/to/this/project
> su nesuser   # หรือ ssh เข้าเครื่องด้วย user นี้โดยตรง
> ```
> ดูเหตุผลเต็มๆ ในหัวข้อ "ไม่มีจอจริง" ด้านล่าง

1. ดาวน์โหลด BizHawk build สำหรับ Linux จาก [official releases](https://github.com/TASEmulators/BizHawk/releases) (เช่น `BizHawk-2.11.1-linux-x64.tar.gz`) มาวางไว้ที่ root ของโปรเจกต์นี้
2. วาง ROM ไฟล์ `.nes` ที่ต้องการไว้ในโฟลเดอร์ `roms/`
3. รันคำสั่งเดียว (เป็น user ธรรมดา — ขั้นตอนติดตั้ง package ข้างในจะขอ sudo เองถ้าจำเป็น):

   ```bash
   ./scripts/report.sh
   ```

   สคริปต์นี้ทำให้ครบในรันเดียว: ติดตั้ง dependency ที่ BizHawk ต้องใช้จริง (`mono-complete`, `libopenal1`, `lsb-release`, `liblua5.4-0`, `ffmpeg`, `xvfb` — ทดสอบยืนยันแล้วว่าครบตามนี้ ไม่ใช่แค่ตามเอกสาร), ตั้ง null ALSA device (server ส่วนใหญ่ไม่มีการ์ดเสียงจริง), แตก tarball ลง `./bizhawk/` (ข้ามอัตโนมัติถ้าแตกไว้แล้ว), เช็ค environment (`doctor.py`), แล้วทดสอบรันจริง 1 ROM (`smoke_test.py`) — จบแล้วสรุปสถานะ **READY**/**NOT READY** ให้ พร้อมเซฟรายงานเป็นไฟล์ `report_<เวลา>.txt` ไว้ด้วย

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

**ยืนยันแล้ว: ใช้ได้จริง** — ทดสอบกับ BizHawk 2.11.1 ตัวจริงบน Ubuntu 24.04 แบบไม่มีจอเลย (รันผ่าน `xvfb-run`) จนได้วิดีโอ 1080x1920 ออกมาสำเร็จจริง ไม่ใช่แค่ทฤษฎี

BizHawk **ไม่มี** headless mode อย่างเป็นทางการ ([ทีมพัฒนายืนยันเอง](https://tasvideos.org/Forum/Topics/20293)) วิธีที่ใช้คือ `xvfb-run` (จอเสมือนใน memory) ซึ่งใช้ได้ แต่ระหว่างทดสอบเจอ 3 จุดที่ทำให้ BizHawk **ค้างตลอดไปแบบไม่มี error** (โชว์ dialog popup ที่ไม่มีใครกด OK ได้เพราะไม่มีจอ) — `scripts/setup.sh` แก้ให้ครบทั้ง 3 จุดนี้แล้วโดยอัตโนมัติ:

1. **รันเป็น root** — BizHawk โชว์ dialog เตือน "running as root" ทุกครั้งที่ไม่มี `$DISPLAY`. **ไม่มีทางปิดผ่าน config ได้** (ลองแล้ว config.ini ที่ pre-seed ไปโดน BizHawk มองว่า "corrupted" เพราะ schema ไม่ตรงเวอร์ชัน) ทางแก้เดียวที่ยืนยันว่าได้ผล: **ห้ามรันเป็น root** ต้องสร้าง user ธรรมดารัน `smoke_test.py`/`batch_generate.py` แทน (แต่ `setup.sh` เองรันเป็น root/sudo ได้ปกติ เพราะแค่ติดตั้ง package)
2. **ไม่มีการ์ดเสียงจริง** (ปกติของ server ทุกเครื่อง) — โชว์ dialog "Couldn't initialize sound device!" แก้ด้วย null ALSA device ซึ่ง `setup.sh` เขียนให้ทั้ง `/etc/asound.conf` และ `~/.asoundrc`
3. **ขาด native Lua library** — โชว์ dialog "Native Lua dynamic library was unable to be loaded" ทั้งที่มี `mono-complete` ครบแล้ว ต้องมี package `liblua5.4-0` แยกต่างหาก (README ของ BizHawk เขียนแค่ "Lua 5.4" เฉยๆ ไม่ได้บอกชื่อ package บน apt ตรงๆ) — `setup.sh` ติดตั้งให้แล้ว

`doctor.py`/`batch_generate.py` preflight เช็คข้อ 1 (root) ให้อัตโนมัติแล้ว ข้อ 2-3 เป็นเรื่อง package ที่ `setup.sh` จัดการให้ครบ — **สรุปคือแค่รัน `./scripts/report.sh` ตามขั้นตอนใน Setup ด้านบน (ผ่าน user ธรรมดา ไม่ใช่ root) ก็ใช้งานได้จริงแล้ว**

**ถ้ายัง fail หลังรัน `setup.sh`** (เช่น distro ที่ package ชื่อไม่ตรง หรือ error อื่นที่ไม่เจอตอนทดสอบ): ก๊อปรายงานจาก `./scripts/report.sh` ส่งกลับมาได้เลย หรือ debug เองด้วยการ screenshot จอเสมือนตอนที่มันค้าง (`ffmpeg -f x11grab -i :<เลข display จาก ps aux | grep Xvfb> -frames:v 1 out.png`) แล้วดูว่า dialog อะไรค้างอยู่

## หมายเหตุ

- `generic_preview.lua` ใช้การสุ่ม input แบบมี bias (เดินหน้าเป็นหลัก, บางครั้งกระโดด/attack) เพื่อให้ดูเหมือนมีคนเล่นจริง และจะพยายามกด Start/A ในช่วงแรกเพื่อผ่าน title screen
- เหมาะกับ ROM ส่วนใหญ่ที่เป็นเกม platformer/action ที่เดินหน้าได้ อาจไม่เหมาะกับเกมแนว puzzle/menu-heavy
- โฟลเดอร์ screenshot ระหว่างประมวลผล (`frames_dir`) ถูกสร้าง/เคลียร์โดย `batch_generate.py` ก่อนรันทุกครั้ง แล้วส่ง path ให้ `generic_preview.lua` ผ่าน environment variable `NES_FRAMES_DIR` (มี fallback เป็นไฟล์ `scripts/.frames_dir` เผื่อ BizHawk build บาง build บล็อค `os.getenv`) — ไม่ได้พึ่งการ `mkdir` แบบ relative path จากฝั่ง Lua เพราะ working directory ของ BizHawk คือโฟลเดอร์ติดตั้งของมันเอง ไม่ใช่โฟลเดอร์โปรเจกต์นี้
- BizHawk build ที่ทดสอบ end-to-end จริง (ไม่ใช่แค่ syntax check): `BizHawk-2.11.1-linux-x64` บน Ubuntu 24.04, headless ผ่าน `xvfb-run`, ได้ไฟล์วิดีโอ 1080x1920/30fps/15s ออกมาสำเร็จ

## Troubleshooting

รัน `./scripts/report.sh` ก่อนเสมอเมื่อเจอปัญหา แล้วก๊อปข้อความทั้งหมดที่มันพิมพ์ (หรือเนื้อหาไฟล์ `report_*.txt` ที่มันเซฟไว้) ส่งกลับมาได้เลย — มันรวมข้อมูล system, tool versions, ROM, ผล `doctor.py`, และผล `smoke_test.py` ไว้ในที่เดียว ไม่ต้องรันหลายคำสั่งเอง
