-- generic_preview.lua
-- ใช้ได้กับ NES ROM ทุกเกม สุ่มปุ่ม + capture เฟรมเป็น screenshot
--
-- โฟลเดอร์ปลายทางสำหรับ screenshot: ไม่ใช้ "os.execute" หา/สร้าง path เอง
-- เพราะ BizHawk บาง build บล็อค os.execute ไว้ (ต้องเปิด Lua "unsafe" mode)
-- และเพราะ path แบบ relative ("frames") จะถูกตีความจาก working directory
-- ของ BizHawk เอง (คือโฟลเดอร์ที่ติดตั้ง ไม่ใช่โฟลเดอร์โปรเจกต์นี้) ทำให้
-- path เพี้ยนได้ ("./frames" ของ Python คนละที่กับ "frames" ของ BizHawk)
--
-- batch_generate.py จะสร้าง/เคลียร์โฟลเดอร์ frames_dir (absolute path) ไว้
-- ให้ล่วงหน้าเสมอ แล้วบอก path นั้นให้ script นี้รู้ด้วย 2 ทาง (ลองตามลำดับ):
--   1) environment variable NES_FRAMES_DIR
--   2) ไฟล์ ".frames_dir" ที่วางไว้ข้างๆ ไฟล์ .lua นี้เอง (เผื่อ os.getenv
--      ถูกบล็อคเหมือนกัน — ใช้ debug.getinfo หา path ของสคริปต์นี้แทน ซึ่ง
--      ไม่ขึ้นกับ working directory)
-- ถ้าหาไม่เจอทั้งคู่ fallback เป็น "frames" (relative) เหมือน behavior เดิม
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

local frame = 0
local duration = 900  -- 15 วิ @ 60fps
math.randomseed(os.time())

local held = {}

function randomize_input()
    -- เปลี่ยนปุ่มทุก ~20 เฟรม ให้ดูเหมือนมีคนเล่น ไม่กระตุก
    if frame % 20 == 0 then
        held = {}
        held.Right = true              -- bias เดินหน้า ใช้ได้กับเกมส่วนใหญ่
        if math.random() < 0.5 then held.A = true end
        if math.random() < 0.15 then held.B = true end
        if math.random() < 0.1 then held.Up = true end
        if math.random() < 0.05 then held.Down = true end
    end
    -- กด Start/A ช่วงแรกไว้ผ่าน title screen
    if frame < 80 and frame % 15 < 4 then
        held.Start = true
        held.A = true
    end
end

while frame < duration do
    randomize_input()
    joypad.set(held)
    client.screenshot(string.format("%s/f%04d.png", outdir, frame))
    frame = frame + 1
    emu.frameadvance()
end

console.log("done")
client.exit()
