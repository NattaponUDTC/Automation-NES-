-- smoke_test.lua
-- ทดสอบเร็ว: รัน ROM ~30 เฟรมแล้ว capture screenshot 1 รูปแล้วออกทันที
-- ใช้คู่กับ scripts/smoke_test.py เพื่อเช็คว่า BizHawk รันได้จริงบนเครื่องนี้
-- (โดยเฉพาะกรณีไม่มีจอจริง รันผ่าน Xvfb) ก่อนสั่ง batch_generate.py ที่ใช้เวลานานกว่า
--
-- อ่าน path ปลายทางแบบเดียวกับ generic_preview.lua (ดูคอมเมนต์ที่นั่น)
local function script_dir()
    local src = debug.getinfo(1, "S").source
    local path = src:match("^@(.*)$") or src
    return path:match("^(.*)[/\\][^/\\]*$") or "."
end

local function read_frames_dir_file()
    local ok, f = pcall(io.open, script_dir() .. "/.frames_dir", "r")
    if ok and f then
        local line = f:read("*l")
        f:close()
        return line
    end
    return nil
end

local outdir = os.getenv("NES_FRAMES_DIR") or read_frames_dir_file() or "frames"

for frame = 1, 30 do
    joypad.set({Right = true})
    emu.frameadvance()
end

client.screenshot(outdir .. "/smoke.png")
console.log("SMOKE_TEST_OK")
client.exit()
