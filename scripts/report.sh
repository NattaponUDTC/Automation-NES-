#!/usr/bin/env bash
# scripts/report.sh
#
# รันครั้งเดียว รวบรวมทุกอย่าง (system info + setup + doctor + smoke test)
# เป็นรายงานเดียว ก๊อปข้อความที่ terminal พิมพ์ออกมาทั้งหมด (หรือเนื้อหาไฟล์
# report_*.txt ที่มันเซฟไว้) ส่งกลับไปที่แชทได้เลย ไม่ต้องรันทีละสคริปต์เอง
#
# ใช้: ./scripts/report.sh
set -uo pipefail  # ไม่ใช้ -e เพราะต้องรันให้ครบทุก step แม้บาง step fail แล้วสรุปผลรวม

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

REPORT_FILE="$PROJECT_ROOT/report_$(date +%Y%m%d_%H%M%S).txt"

# ทุกอย่างที่ print ต่อจากบรรทัดนี้ไปทั้งขึ้นจอและเซฟลงไฟล์พร้อมกัน
exec > >(tee "$REPORT_FILE") 2>&1

section() {
    echo ""
    echo "===== $1 ====="
}

echo "NES Reel Preview Generator — Diagnostic Report"
echo "Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

section "System"
uname -a
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Distro: ${PRETTY_NAME:-unknown}"
fi

section "Tool versions"
echo -n "ffmpeg:   "; ffmpeg -version 2>&1 | head -n1 || echo "NOT FOUND"
echo -n "mono:     "; mono --version 2>&1 | head -n1 || echo "NOT FOUND"
echo -n "xvfb-run: "; command -v xvfb-run || echo "NOT FOUND"
echo "DISPLAY=${DISPLAY:-<unset>}"

section "ROMs"
if [ -d roms ]; then
    ROM_COUNT=$(find roms -maxdepth 1 -iname '*.nes' 2>/dev/null | wc -l)
    echo "พบไฟล์ .nes: $ROM_COUNT ไฟล์"
    find roms -maxdepth 1 -iname '*.nes' -printf '  - %f\n' 2>/dev/null | head -20
else
    echo "ไม่พบโฟลเดอร์ roms/"
    ROM_COUNT=0
fi

section "setup.sh"
if [ "$(uname -s)" != "Linux" ]; then
    echo "(ข้าม — setup.sh รองรับเฉพาะ Linux)"
elif [ -x "$PROJECT_ROOT/bizhawk/EmuHawkMono.sh" ]; then
    echo "(ข้าม — พบ ./bizhawk/EmuHawkMono.sh อยู่แล้ว ถ้าต้องการติดตั้ง/แตกไฟล์ใหม่ รันเอง: ./scripts/setup.sh)"
else
    ./scripts/setup.sh
fi

section "doctor.py"
python3 scripts/doctor.py
DOCTOR_EXIT=$?

section "smoke_test.py"
if [ "$DOCTOR_EXIT" -eq 0 ]; then
    python3 scripts/smoke_test.py
    SMOKE_EXIT=$?
else
    echo "(ข้าม — doctor.py ยังไม่ผ่าน แก้ปัญหาในรายงานด้านบนก่อน)"
    SMOKE_EXIT=2
fi

section "สรุปผล"
if [ "$DOCTOR_EXIT" -ne 0 ]; then
    echo "สถานะ: NOT READY — doctor.py เจอปัญหา (ดูรายละเอียดด้านบน)"
elif [ "$SMOKE_EXIT" -eq 0 ]; then
    echo "สถานะ: READY — smoke test ผ่าน รันได้เลย: python3 scripts/batch_generate.py"
else
    echo "สถานะ: NOT READY — doctor.py ผ่านแต่ smoke test (รัน BizHawk จริง) fail"
fi

echo ""
echo "บันทึกรายงานไว้ที่: $REPORT_FILE"
echo "ก๊อปข้อความทั้งหมดด้านบนนี้ (ตั้งแต่ 'Diagnostic Report' ถึงตรงนี้) ส่งกลับไปที่แชทได้เลย"

if [ "$DOCTOR_EXIT" -ne 0 ] || [ "$SMOKE_EXIT" -ne 0 ]; then
    exit 1
fi
exit 0
