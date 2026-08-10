"""
Batch generate 15s vertical reel preview จาก NES ROM ทุกไฟล์ในโฟลเดอร์
ต้องมี: BizHawk (EmuHawk.exe), ffmpeg ใน PATH
"""

import subprocess
import os
import glob
import shutil
import sys
import json

# ---------- CONFIG ----------
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

BIZHAWK = CFG["bizhawk_exe"]
LUA = os.path.join(os.path.dirname(__file__), "generic_preview.lua")
ROM_DIR = CFG["rom_dir"]
OUT_DIR = CFG["output_dir"]
FRAMES_DIR = CFG["frames_dir"]
TIMEOUT_SEC = CFG.get("timeout_sec", 60)
LOG_PATH = os.path.join(OUT_DIR, "batch_log.txt")
# -----------------------------

os.makedirs(OUT_DIR, exist_ok=True)


def log(msg):
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def process_rom(rom_path):
    name = os.path.splitext(os.path.basename(rom_path))[0]
    reel_mp4 = os.path.join(OUT_DIR, f"{name}_reel.mp4")

    if os.path.exists(reel_mp4):
        log(f"[{name}] มีไฟล์อยู่แล้ว ข้าม")
        return

    log(f"[{name}] เริ่ม...")

    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)

    try:
        subprocess.run(
            [BIZHAWK, f"--lua={LUA}", rom_path],
            timeout=TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        log(f"[{name}] TIMEOUT - ข้าม (เกมอาจค้าง)")
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
    log(f"[{name}] เสร็จ -> {reel_mp4}")


def main():
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
