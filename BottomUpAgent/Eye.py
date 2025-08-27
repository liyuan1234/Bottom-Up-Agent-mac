import cv2
import numpy as np
import mss
# import win32gui
import pyautogui
import datetime




class Eye:
    def __init__(self, config):
        self.window_name = config["game_name"]
        self.left = None
        self.top = None
        self.width = config['eye']['width']
        self.height = config['eye']['height']


    def get_screenshot_cv(self):
        if self.window_name:
            if platform.system == 'Windows':
                hwnd = win32gui.FindWindow(None, self.window_name)
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)

            elif platform.system == 'Darwin':
                from .mac_utils import get_game_coordinates, get_window_with_title

                hwnd = get_window_with_title(self.window_name)
                left, height, top, width= get_game_coordinates(self.window_name)
            if not hwnd:
                print("Window not found.")
                return None



            # Take screenshot
            with mss.mss() as sct:
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
                screenshot = sct.grab(monitor)

                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)


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
    