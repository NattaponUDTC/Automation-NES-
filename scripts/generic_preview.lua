-- generic_preview.lua
-- ใช้ได้กับ NES ROM ทุกเกม สุ่มปุ่ม + capture เฟรมเป็น screenshot
local frame = 0
local duration = 900  -- 15 วิ @ 60fps
local outdir = "frames"

os.execute("mkdir " .. outdir)
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
