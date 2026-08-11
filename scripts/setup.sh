#!/usr/bin/env bash
# scripts/setup.sh
#
# ติดตั้งสิ่งที่จำเป็นสำหรับรัน NES Reel Preview Generator บน Linux
# (รายการนี้ verify แล้วจริงด้วย BizHawk 2.11.1 บน Ubuntu 24.04 แบบ headless
# ผ่าน xvfb-run — ไม่ใช่แค่ตามเอกสาร ทุกตัวจำเป็นจริงเพื่อไม่ให้ BizHawk ค้าง):
#   - mono-complete, libopenal1, lsb-release  (runtime dependencies หลักตาม README ของ BizHawk)
#   - liblua5.4-0                             (native Lua lib — ขาดแล้ว BizHawk ค้างที่ dialog
#                                               "Native Lua dynamic library was unable to be loaded")
#   - ffmpeg, xvfb                            (ประกอบวิดีโอ + รัน BizHawk แบบไม่มีจอ)
#   - null ALSA device (/etc/asound.conf + ~/.asoundrc) — เครื่อง server ไม่มีการ์ดเสียงจริง
#     ถ้าไม่มี BizHawk จะค้างที่ dialog "Couldn't initialize sound device!"
#   - แตก BizHawk-*.tar.gz (ถ้ามีวางไว้ที่ root ของโปรเจกต์) ลงโฟลเดอร์ ./bizhawk
#
# หมายเหตุสำคัญ: รัน BizHawk แบบ headless "ห้ามรันเป็น root" — ถ้ารันเป็น root
# BizHawk จะโชว์ dialog เตือน "running as root" ที่ต้องกด OK เอง (ไม่มีทาง
# auto-dismiss ได้แบบ config) ทำให้ batch_generate.py ค้างรอตลอดไปแบบไม่มี error
# ถ้าจำเป็นต้องรันเป็น root จริงๆ (เช่นบาง container) ให้สร้าง user ธรรมดารันแทน
#
# ใช้: ./scripts/setup.sh [path/to/BizHawk-*.tar.gz]
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "== NES Reel Preview Generator: setup =="

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "สคริปต์นี้รองรับเฉพาะ Linux เท่านั้น (Windows ใช้ EmuHawk.exe ตรงๆ ได้เลย ไม่ต้องรันสคริปต์นี้)"
    exit 1
fi

# ---------- 1. system packages ----------
if command -v apt-get >/dev/null 2>&1; then
    echo "-- ติดตั้ง system packages ผ่าน apt (ต้องใช้ sudo) --"
    SUDO=""
    if [[ $EUID -ne 0 ]]; then
        SUDO="sudo"
    fi
    $SUDO apt-get update
    # mono-complete + libopenal1 + lsb-release: ตาม README ของ TASEmulators/BizHawk
    # liblua5.4-0: ขาดไม่ได้จริง — ทดสอบแล้วเจอ BizHawk ค้างที่ dialog error ถ้าไม่มี
    $SUDO apt-get install -y mono-complete libopenal1 lsb-release liblua5.4-0 ffmpeg xvfb || {
        echo "ติดตั้งบาง package ไม่สำเร็จ (มักเป็น mono-complete ที่ repo เริ่มต้นของ distro ไม่มี)"
        echo "ถ้า mono-complete หาไม่เจอ ให้เพิ่ม official Mono apt repo ก่อน ดู: https://www.mono-project.com/download/stable/#download-lin"
    }
else
    echo "ไม่พบ apt-get (ไม่ใช่ Debian/Ubuntu) กรุณาติดตั้งเองตาม package manager ของ distro:"
    echo "  mono-complete, libopenal1, lsb-release, liblua5.4-0 (หรือเทียบเท่า), ffmpeg, xvfb (ให้ xvfb-run ใช้ได้)"
fi

# ---------- 1b. null ALSA device ----------
# server ส่วนใหญ่ไม่มีการ์ดเสียงจริง ถ้าไม่มี ALSA device เลย BizHawk จะค้างที่
# dialog "Couldn't initialize sound device!" ตอนเปิดแบบ headless (verify แล้วจริง)
# เขียนทั้งระดับระบบ (/etc/asound.conf ถ้ามีสิทธิ์) และระดับ user (~/.asoundrc)
# กันไว้สองชั้น เผื่อ setup.sh รันเป็น user ที่ไม่มี sudo
ALSA_NULL_CONF='pcm.!default {
    type null
}
ctl.!default {
    type null
}'

echo "-- ตั้งค่า null ALSA device กัน BizHawk ค้างเรื่องเสียง --"
if [[ -f /etc/asound.conf ]]; then
    echo "(ข้าม /etc/asound.conf — มีอยู่แล้ว ไม่เขียนทับ)"
elif [[ $EUID -eq 0 ]]; then
    echo "$ALSA_NULL_CONF" > /etc/asound.conf
elif command -v sudo >/dev/null 2>&1; then
    echo "$ALSA_NULL_CONF" | sudo tee /etc/asound.conf >/dev/null || true
fi
if [[ ! -f "$HOME/.asoundrc" ]]; then
    echo "$ALSA_NULL_CONF" > "$HOME/.asoundrc"
fi

# ---------- 2. extract BizHawk ----------
TARBALL="${1:-}"
if [[ -z "$TARBALL" ]]; then
    TARBALL="$(find "$PROJECT_ROOT" -maxdepth 1 -iname 'BizHawk-*.tar.gz' | head -n1 || true)"
fi

if [[ -n "$TARBALL" && -f "$TARBALL" ]]; then
    echo "-- แตกไฟล์ $TARBALL -> ./bizhawk --"
    rm -rf "$PROJECT_ROOT/bizhawk"
    mkdir -p "$PROJECT_ROOT/bizhawk"
    tar -xzf "$TARBALL" -C "$PROJECT_ROOT/bizhawk" --strip-components=1
    chmod +x "$PROJECT_ROOT/bizhawk/EmuHawkMono.sh" 2>/dev/null || \
        echo "หมายเหตุ: ไม่พบ EmuHawkMono.sh ตรงตำแหน่งที่คาด ตรวจสอบโครงสร้างใน ./bizhawk เอง"
else
    echo "-- ไม่พบ BizHawk-*.tar.gz ที่ root โปรเจกต์ ข้ามขั้นตอนแตกไฟล์ --"
    echo "   ดาวน์โหลดได้จาก https://github.com/TASEmulators/BizHawk/releases แล้วรัน:"
    echo "   ./scripts/setup.sh path/to/BizHawk-x.y.z-linux-x64.tar.gz"
fi

mkdir -p "$PROJECT_ROOT/roms" "$PROJECT_ROOT/output"

echo ""
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  กำลังรันเป็น root — BizHawk แบบ headless จะค้างตลอดไปที่ dialog เตือน"
    echo "   \"running as root\" ที่ไม่มีทางกด OK เองได้ (ทดสอบยืนยันแล้วจริง)"
    echo "   แนะนำให้สร้าง user ธรรมดารัน batch_generate.py/smoke_test.py แทน เช่น:"
    echo "     useradd -m nesuser && chown -R nesuser:nesuser '$PROJECT_ROOT'"
    echo "     su nesuser -c 'cd $PROJECT_ROOT && python3 scripts/smoke_test.py'"
fi
echo "== เสร็จแล้ว รันตรวจสอบด้วย: python3 scripts/doctor.py =="
