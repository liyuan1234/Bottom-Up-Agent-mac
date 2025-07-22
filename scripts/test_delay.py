import pyautogui
import time
from PIL import ImageGrab
import mss
import numpy as np

# 游戏按钮位置（根据你的分辨率调整）
click_pos = (895, 900)
check_region = (649, 218, 1087, 617)
monitor_region = {"top": 649, "left": 218, "width": 400, "height": 400}
pyautogui.PAUSE = 0  # 禁用默认延迟


# 测试准备
input("请打开 Civ5 并将鼠标放开按钮区域，按回车开始测试...")

with mss.mss() as sct:
    # === 1. 基线图像（点击前） ===
    baseline = np.array(sct.grab(monitor_region))

    # === 2. 点击并记录时间 ===
    start_time = time.perf_counter()
    pyautogui.click(click_pos)  # 点击按钮
    click_delay = time.perf_counter() - start_time
    

    

    # === 3. 连续高频截图，检测变化 ===
    screenshot_count = 0
    timeout = 2.0
    while True:
        end_time = time.perf_counter()
        img = np.array(sct.grab(monitor_region))
        
        screenshot_count += 1

        if not np.array_equal(img, baseline):
            
            break

        if time.perf_counter() - start_time > timeout:
            end_time = None
            break

# === 4. 输出结果 ===
if end_time:
    raw_delay = (end_time - start_time) * 1000
    print(f"点击按钮耗时：{click_delay * 1000:.2f} 毫秒")
    print(f"\n✅ 最终延迟(mss 高精度): {raw_delay:.2f} 毫秒")
    print(f"📸 截图次数：{screenshot_count}")
    
else:
    print("❌ 未检测到变化，可能区域不正确或 Civ5 没有明显响应。")