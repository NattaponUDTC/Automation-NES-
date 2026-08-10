"""
scripts/smoke_test.py — ทดสอบเร็วว่า BizHawk รันได้จริงบนเครื่องนี้หรือไม่
ก่อนสั่ง batch_generate.py ประมวลผลทุก ROM (ซึ่งอาจใช้เวลานานเป็นชั่วโมง)

รันกับ ROM แรกที่เจอใน roms/ เท่านั้น ใช้เวลาไม่กี่วินาที ถ้าเครื่องไม่มีจอจริง
(รันผ่าน Xvfb) นี่คือจุดที่ควรทดสอบก่อน — BizHawk ไม่มี headless mode
อย่างเป็นทางการ (https://tasvideos.org/Forum/Topics/20293) ดังนั้นการรันผ่าน
Xvfb อาจมีปัญหาเรื่อง OpenGL context ที่ยังไม่มีใครยืนยันว่าใช้ได้ 100%

ใช้: python3 scripts/smoke_test.py
"""

import glob
import os
import shutil
import subprocess
import sys

import batch_generate as bg  # ใช้ config/paths/preflight/build_command/build_env ร่วมกัน


def main():
    bg.preflight()

    roms = sorted(glob.glob(os.path.join(bg.ROM_DIR, "*.nes")))
    if not roms:
        print(f"ไม่พบ .nes ไฟล์ใน {bg.ROM_DIR} — วาง ROM อย่างน้อย 1 ไฟล์ก่อนทดสอบ")
        sys.exit(1)

    rom = roms[0]
    print(f"ทดสอบด้วย ROM: {rom}")

    lua = os.path.join(bg.SCRIPT_DIR, "smoke_test.lua")

    if os.path.exists(bg.FRAMES_DIR):
        shutil.rmtree(bg.FRAMES_DIR)
    os.makedirs(bg.FRAMES_DIR, exist_ok=True)

    env = bg.build_env()
    with open(os.path.join(bg.SCRIPT_DIR, ".frames_dir"), "w", encoding="utf-8") as f:
        f.write(bg.FRAMES_DIR + "\n")

    cmd = [bg.BIZHAWK, f"--lua={lua}", rom]
    if bg.wants_xvfb():
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24 -ac"] + cmd

    print("รันคำสั่ง:", " ".join(cmd))
    try:
        result = subprocess.run(cmd, timeout=30, capture_output=True, env=env)
    except subprocess.TimeoutExpired:
        print("[FAIL] BizHawk ไม่ตอบสนองภายใน 30 วิ (timeout)")
        print("ลอง: รันคำสั่งข้างบนเองตรงๆ (ไม่ผ่าน python) เพื่อดู error เต็มๆ")
        sys.exit(1)

    screenshot = os.path.join(bg.FRAMES_DIR, "smoke.png")
    if os.path.exists(screenshot):
        print(f"[OK] BizHawk รันสำเร็จ capture screenshot ได้ที่ {screenshot}")
        print("พร้อมรัน: python3 scripts/batch_generate.py")
    else:
        print("[FAIL] ไม่พบ screenshot — BizHawk อาจรันไม่สำเร็จ")
        print(f"exit code: {result.returncode}")
        print("stdout:", result.stdout.decode(errors="ignore")[-1000:])
        print("stderr:", result.stderr.decode(errors="ignore")[-1000:])
        print("")
        print("ปัญหาที่พบบ่อยเวลารันผ่าน Xvfb (ไม่มีจอจริง):")
        print("  - error เกี่ยวกับ OpenGL/GLX/GL context: สคริปต์นี้ตั้ง")
        print("    LIBGL_ALWAYS_SOFTWARE=1 ให้แล้ว แต่ถ้ายัง fail ลอง export ตัวแปรนี้เอง")
        print("    แล้วรันคำสั่งข้างบนตรงๆ ดูว่า error เปลี่ยนไปไหม")
        print("  - ถ้ายังไม่ได้ ลองรันบนเครื่องที่มี desktop/VNC จริง")
        print("    (ตั้ง $DISPLAY เอง จะข้าม xvfb-run อัตโนมัติ เพราะ use_xvfb=\"auto\")")
        sys.exit(1)


if __name__ == "__main__":
    main()
