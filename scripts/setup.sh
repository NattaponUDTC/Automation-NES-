#!/usr/bin/env bash
# scripts/setup.sh
#
# ติดตั้งสิ่งที่จำเป็นสำหรับรัน NES Reel Preview Generator บน Linux:
#   - mono-complete, libopenal1, lsb-release  (runtime dependencies ของ BizHawk)
#   - ffmpeg, xvfb                            (ประกอบวิดีโอ + รัน BizHawk แบบไม่มีจอ)
#   - แตก BizHawk-*.tar.gz (ถ้ามีวางไว้ที่ root ของโปรเจกต์) ลงโฟลเดอร์ ./bizhawk
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
    # mono-complete คือ runtime dependency หลักของ BizHawk บน Linux
    # (ตาม README ของ TASEmulators/BizHawk: glibc, mono-complete, OpenAL, Lua 5.4, lsb_release)
    $SUDO apt-get install -y mono-complete libopenal1 lsb-release ffmpeg xvfb || {
        echo "ติดตั้งบาง package ไม่สำเร็จ (มักเป็น mono-complete ที่ repo เริ่มต้นของ distro ไม่มี)"
        echo "ถ้า mono-complete หาไม่เจอ ให้เพิ่ม official Mono apt repo ก่อน ดู: https://www.mono-project.com/download/stable/#download-lin"
    }
else
    echo "ไม่พบ apt-get (ไม่ใช่ Debian/Ubuntu) กรุณาติดตั้งเองตาม package manager ของ distro:"
    echo "  mono-complete, libopenal1 (หรือเทียบเท่า), lsb-release, ffmpeg, xvfb (ให้ xvfb-run ใช้ได้)"
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
echo "== เสร็จแล้ว รันตรวจสอบด้วย: python3 scripts/doctor.py =="
