"""
scripts/doctor.py — ตรวจสอบว่า environment พร้อมรัน batch_generate.py หรือยัง
ไม่แก้ไข/ติดตั้งอะไร แค่รายงานผล เช่นเดียวกับ preflight ใน batch_generate.py
แต่ให้รายละเอียดครบกว่า และรันได้แม้ยังไม่มี BizHawk ติดตั้ง

ใช้: python3 scripts/doctor.py
"""

import json
import os
import platform
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# ปิดสี ANSI ถ้า output ไม่ใช่ terminal จริง (เช่นถูก redirect ไปไฟล์/tee
# โดย scripts/report.sh) กันโค้ดสีเพี้ยนๆ ปนอยู่ในรายงานที่จะก๊อปไปวางที่อื่น
if sys.stdout.isatty():
    OK = "\033[32m[OK]\033[0m"
    FAIL = "\033[31m[FAIL]\033[0m"
    WARN = "\033[33m[WARN]\033[0m"
else:
    OK = "[OK]"
    FAIL = "[FAIL]"
    WARN = "[WARN]"


def resolve(path):
    return os.path.normpath(os.path.join(PROJECT_ROOT, os.path.expanduser(path)))


def check(label, ok, detail=""):
    tag = OK if ok else FAIL
    print(f"{tag} {label}" + (f" — {detail}" if detail else ""))
    return ok


def warn(label, detail=""):
    print(f"{WARN} {label}" + (f" — {detail}" if detail else ""))


def main():
    all_ok = True

    if not os.path.exists(CONFIG_PATH):
        check("scripts/config.json exists", False, "หาไม่เจอ")
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    check("scripts/config.json parse ได้", True)

    is_windows = platform.system() == "Windows"
    print(f"\nระบบปฏิบัติการ: {platform.system()} ({platform.machine()})\n")

    # ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    all_ok &= check("ffmpeg อยู่ใน PATH", ffmpeg_path is not None, ffmpeg_path or "ติดตั้งด้วย: sudo apt install ffmpeg")

    # bizhawk
    bizhawk_path = resolve(cfg.get("bizhawk_path", ""))
    exists = os.path.exists(bizhawk_path)
    all_ok &= check(f"bizhawk_path มีอยู่จริง ({bizhawk_path})", exists,
                     None if exists else "รัน ./scripts/setup.sh หรือแก้ path ใน scripts/config.json")

    if exists and not is_windows:
        executable = os.access(bizhawk_path, os.X_OK)
        all_ok &= check("bizhawk_path มี execute permission", executable,
                         None if executable else f"รัน: chmod +x '{bizhawk_path}'")

    # mono (Linux only, needed for EmuHawkMono.sh)
    if not is_windows:
        mono_path = shutil.which("mono")
        needs_mono = not str(bizhawk_path).endswith(".exe")
        if needs_mono:
            all_ok &= check("mono อยู่ใน PATH", mono_path is not None,
                             mono_path or "ติดตั้งด้วย ./scripts/setup.sh (ใช้ mono-complete)")

    # xvfb-run (Linux, only strictly needed if no DISPLAY)
    if not is_windows:
        has_display = bool(os.environ.get("DISPLAY"))
        xvfb_path = shutil.which("xvfb-run")
        if has_display:
            check("DISPLAY ตั้งค่าไว้แล้ว (ไม่จำเป็นต้องใช้ xvfb-run)", True, os.environ.get("DISPLAY"))
        else:
            all_ok &= check("xvfb-run อยู่ใน PATH (จำเป็นเพราะไม่มี DISPLAY)", xvfb_path is not None,
                             xvfb_path or "ติดตั้งด้วย: sudo apt install xvfb")

    # roms
    rom_dir = resolve(cfg.get("rom_dir", "./roms"))
    rom_dir_exists = os.path.isdir(rom_dir)
    check(f"โฟลเดอร์ ROM มีอยู่ ({rom_dir})", rom_dir_exists)
    if rom_dir_exists:
        nes_files = [f for f in os.listdir(rom_dir) if f.lower().endswith(".nes")]
        if nes_files:
            check(f"พบไฟล์ .nes ในโฟลเดอร์ ROM", True, f"{len(nes_files)} ไฟล์")
        else:
            warn("ยังไม่มีไฟล์ .nes ในโฟลเดอร์ ROM", f"วาง ROM ไว้ที่ {rom_dir}")

    # output dir writable
    output_dir = resolve(cfg.get("output_dir", "./output"))
    os.makedirs(output_dir, exist_ok=True)
    writable = os.access(output_dir, os.W_OK)
    all_ok &= check(f"เขียนไฟล์ลง output_dir ได้ ({output_dir})", writable)

    print("")
    if all_ok:
        print(f"{OK} พร้อมรัน: python3 scripts/batch_generate.py")
    else:
        print(f"{FAIL} ยังมีปัญหาที่ต้องแก้ก่อน (ดูรายการ [FAIL] ด้านบน)")
        sys.exit(1)


if __name__ == "__main__":
    main()
