"""
Batch generate 15s vertical reel preview จาก NES ROM ทุกไฟล์ในโฟลเดอร์
ต้องมี: BizHawk (EmuHawk.exe บน Windows / EmuHawkMono.sh บน Linux+mono), ffmpeg ใน PATH

รัน `python scripts/doctor.py` ก่อนถ้าไม่แน่ใจว่า environment พร้อมหรือยัง
"""

import platform
import shutil
import subprocess
import os
import glob
import sys
import json

# ---------- CONFIG ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)


def resolve(path):
    """path ใน config.json เป็น relative ต่อ project root ได้ (เช่น ./roms)"""
    return os.path.normpath(os.path.join(PROJECT_ROOT, os.path.expanduser(path)))


BIZHAWK = resolve(CFG["bizhawk_path"])
LUA = os.path.join(SCRIPT_DIR, "generic_preview.lua")
ROM_DIR = resolve(CFG["rom_dir"])
OUT_DIR = resolve(CFG["output_dir"])
FRAMES_DIR = resolve(CFG["frames_dir"])
TIMEOUT_SEC = CFG.get("timeout_sec", 60)
USE_XVFB = str(CFG.get("use_xvfb", "auto")).lower()
LOG_PATH = os.path.join(OUT_DIR, "batch_log.txt")
# -----------------------------

os.makedirs(OUT_DIR, exist_ok=True)


def log(msg):
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def wants_xvfb():
    if platform.system() == "Windows":
        return False
    if USE_XVFB in ("false", "0", "no", "off"):
        return False
    if USE_XVFB in ("true", "1", "yes", "on"):
        return True
    # auto: ใช้ xvfb-run เฉพาะตอนไม่มี display จริง (เช่นรันบน server/CI)
    return not os.environ.get("DISPLAY")


def preflight():
    """เช็คให้ครบก่อนเริ่ม batch จริง เพื่อไม่ให้พังกลางทางแบบเงียบๆ"""
    problems = []

    if not os.path.exists(BIZHAWK):
        problems.append(
            f"ไม่พบ BizHawk ที่ '{BIZHAWK}' (config: bizhawk_path='{CFG['bizhawk_path']}')\n"
            f"  -> รัน scripts/setup.sh เพื่อแตก BizHawk tarball หรือแก้ path ใน scripts/config.json"
        )
    elif platform.system() != "Windows" and not os.access(BIZHAWK, os.X_OK):
        problems.append(f"'{BIZHAWK}' ไม่มี permission รัน (execute bit) ลอง: chmod +x '{BIZHAWK}'")

    if shutil.which("ffmpeg") is None:
        problems.append("ไม่พบ ffmpeg ใน PATH ติดตั้งด้วย: sudo apt install ffmpeg (Linux) หรือดาวน์โหลดจาก ffmpeg.org")

    if wants_xvfb() and shutil.which("xvfb-run") is None:
        problems.append("ไม่พบ xvfb-run ใน PATH (จำเป็นเพราะไม่มี DISPLAY) ติดตั้งด้วย: sudo apt install xvfb")

    if platform.system() != "Windows" and shutil.which("mono") is None and not BIZHAWK.endswith(".exe"):
        problems.append("ไม่พบ mono ใน PATH ซึ่ง EmuHawkMono.sh ต้องใช้ ติดตั้งด้วย scripts/setup.sh")

    if not os.path.isdir(ROM_DIR):
        problems.append(f"ไม่พบโฟลเดอร์ ROM '{ROM_DIR}'")

    if problems:
        log("Preflight check ไม่ผ่าน:")
        for p in problems:
            log(f"  - {p}")
        log("\nรัน `python scripts/doctor.py` เพื่อดูรายละเอียด แล้วแก้ก่อนรันใหม่")
        sys.exit(1)


def build_command(rom_path):
    cmd = [BIZHAWK, f"--lua={LUA}", rom_path]
    if wants_xvfb():
        cmd = ["xvfb-run", "-a"] + cmd
    return cmd


def process_rom(rom_path):
    name = os.path.splitext(os.path.basename(rom_path))[0]
    reel_mp4 = os.path.join(OUT_DIR, f"{name}_reel.mp4")

    if os.path.exists(reel_mp4):
        log(f"[{name}] มีไฟล์อยู่แล้ว ข้าม")
        return

    log(f"[{name}] เริ่ม...")

    # เคลียร์แล้วสร้างโฟลเดอร์ frames ใหม่ทุกครั้ง ก่อนสั่ง BizHawk
    # (generic_preview.lua เขียน screenshot ลงโฟลเดอร์นี้ผ่าน env var
    # NES_FRAMES_DIR ด้านล่าง ไม่ต้องพึ่ง mkdir จากฝั่ง Lua)
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR, exist_ok=True)

    env = dict(os.environ)
    env["NES_FRAMES_DIR"] = FRAMES_DIR

    # fallback เผื่อ env var เข้าไม่ถึง Lua sandbox: เขียน path ไว้ในไฟล์
    # ข้างๆ generic_preview.lua ให้สคริปต์อ่านเอง (ดูคอมเมนต์ในไฟล์ .lua)
    with open(os.path.join(SCRIPT_DIR, ".frames_dir"), "w", encoding="utf-8") as f:
        f.write(FRAMES_DIR + "\n")

    cmd = build_command(rom_path)
    try:
        result = subprocess.run(
            cmd,
            timeout=TIMEOUT_SEC,
            capture_output=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            log(f"[{name}] BizHawk exit code {result.returncode}: "
                f"{result.stderr.decode(errors='ignore')[-300:]}")
    except subprocess.TimeoutExpired:
        log(f"[{name}] TIMEOUT - ข้าม (เกมอาจค้าง)")
        return
    except FileNotFoundError as e:
        log(f"[{name}] หา executable ไม่เจอ: {e}")
        return

    if not os.path.exists(FRAMES_DIR) or not os.listdir(FRAMES_DIR):
        log(f"[{name}] ไม่มีเฟรม ข้าม")
        return

    raw_mp4 = os.path.join(OUT_DIR, f"{name}_raw.mp4")

    # ประกอบ screenshot -> วิดีโอ
    r1 = subprocess.run([
        "ffmpeg", "-y", "-framerate", "60",
        "-i", os.path.join(FRAMES_DIR, "f%04d.png"),
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        raw_mp4
    ], capture_output=True)

    if r1.returncode != 0:
        log(f"[{name}] ffmpeg step1 error: {r1.stderr.decode(errors='ignore')[-300:]}")
        return

    # แปลงเป็น reel 1080x1920 (nearest-neighbor scale เพื่อรักษาความคม pixel art)
    r2 = subprocess.run([
        "ffmpeg", "-y", "-i", raw_mp4, "-vf",
        "scale=1080:-2:flags=neighbor,pad=1080:1920:0:(1920-ih)/2:color=black",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
        reel_mp4
    ], capture_output=True)

    if r2.returncode != 0:
        log(f"[{name}] ffmpeg step2 error: {r2.stderr.decode(errors='ignore')[-300:]}")
        return

    os.remove(raw_mp4)
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    log(f"[{name}] เสร็จ -> {reel_mp4}")


def main():
    preflight()

    roms = sorted(glob.glob(os.path.join(ROM_DIR, "*.nes")))
    if not roms:
        log(f"ไม่พบ .nes ไฟล์ใน {ROM_DIR}")
        sys.exit(1)

    log(f"พบ {len(roms)} ROM เริ่มประมวลผล...")

    for rom in roms:
        process_rom(rom)

    log("ทำครบทุก ROM แล้ว")


if __name__ == "__main__":
    main()
