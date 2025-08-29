import cv2
import numpy as np
import mss
# import win32gui
import pyautogui
import datetime

from .mac_utils import getGameCoordinates, get_window_with_title



class Eye:
    def __init__(self, config):
        self.window_name = config["game_name"]
        self.left = None
        self.top = None
        self.width = config['eye']['width']
        self.height = config['eye']['height']


    def get_screenshot_cv(self):
        if self.window_name:
            # hwnd = win32gui.FindWindow(None, self.window_name) 
            hwnd = get_window_with_title(self.window_name)
            if not hwnd:
                print("Window not found.")
                return None

            # left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            left, height, top, width= getGameCoordinates(self.window_name)

            # Take screenshot
            with mss.mss() as sct:
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
                screenshot = sct.grab(monitor)

                ### liyuan code
                save_screenshot = 1
                if save_screenshot:
                    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f'/Users/liyuan/Library/Mobile Documents/com~apple~CloudDocs/iclouddrive/Bottom-Up-Agent/BottomUpAgent/screenshots/{filename}.png'
                    mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)

                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)

            # Save screenshot for debugging
            # now = time.strftime("%Y-%m-%d-%H-%M-%S")
            # logger.log_img_cv(img, f"{now}.png")
            
            # Update window position
            self.left = left
            self.top = top

            # img = cv2.resize(img, (self.width, self.height))
    
            return img

        else:
            print("Window name not set")
            return None

    def detect_acted_cv(self, last_screenshot_cv, current_screenshot_cv):
        if last_screenshot_cv is None:
            return True
        last_gray = cv2.cvtColor(last_screenshot_cv, cv2.COLOR_RGB2GRAY)
        current_gray = cv2.cvtColor(current_screenshot_cv, cv2.COLOR_RGB2GRAY)

        diff = cv2.absdiff(last_gray, current_gray)
        _, diff = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        change_ratio = np.sum(diff) / (diff.shape[0] * diff.shape[1] * 255)
        print(f"Change ratio: {change_ratio}")
        if change_ratio > 0.015:
            return True
        return False
    