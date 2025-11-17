import time
from queue import Empty

import numpy as np
import pyautogui
from utils import click
from utils import extract_text_and_positions, ScreenshotTaker, count_hsv_pixels, load_toml_as_dict

debug = load_toml_as_dict("cfg/general_config.toml")['super_debug'] == "yes"


class LobbyAutomation:
    def __init__(self, frame_queue):
        self.Screenshot = ScreenshotTaker()
        self.coords_cfg = load_toml_as_dict("./cfg/lobby_config.toml")
        self.frame_queue = frame_queue

    @staticmethod
    def check_for_idle(frame):
        screenshot = frame
        screenshot = screenshot.crop((420 * 2, 400 * 2, 1050 * 2, 580 * 2))  #c
        text = extract_text_and_positions(np.array(screenshot))
        idle_state = 'idle disconnect' in text.keys()
        print('Idle state:', idle_state)
        if idle_state:
            if 'reload' in text.keys():
                x, y = int(text['reload']['center'][0])//2, int(text['reload']['center'][1])//2
                print('Clicking ({}, {}) to RELOAD from idle disconnect.'.format(x, y))
                click(480, 550) #c
            else:
                print('Couldn\'t find RELOAD button, proceeding.')

    def select_brawler(self, brawler):
        print('Selecting brawler.')
        x, y = self.coords_cfg['lobby']['brawlers_btn'][0], self.coords_cfg['lobby']['brawlers_btn'][1]
        print('Clicking ({}, {}) for brawler selection button.'.format(x, y))
        click(x, y)
        c = 0
        for i in range(50):
            try:
                screenshot = self.frame_queue.get(timeout=1)
            except Empty:
                continue

            screenshot = screenshot.resize((int(screenshot.width * 0.65), int(screenshot.height * 0.65)))
            screenshot = np.array(screenshot)
            print("Extracting text on current screen...")
            results = extract_text_and_positions(screenshot)
            reworked_results = {}
            for key in results.keys():
                orig_key = key
                for symbol in [' ', '-', '.', "&"]:
                    key = key.replace(symbol, "")
                if key == "shey":
                    key = "shelly"
                reworked_results[key] = results[orig_key]
            print("All detected text while looking for brawler name:", reworked_results.keys())
            if brawler in reworked_results.keys():
                print("Found brawler", brawler)
                x, y = reworked_results[brawler]['center']
                x, y = x / 0.65 / 2, y / 0.65 / 2  # Rescale back and divide due to Mac system
                print('Clicking ({}, {}) to select {}.'.format(x, y, brawler))
                click(x, y)
                time.sleep(4)
                select_x, select_y = self.coords_cfg['lobby']['select_btn'][0], self.coords_cfg['lobby']['select_btn'][
                    1]
                print('Clicking ({}, {}) to confirm select and use {}'.format(select_x, select_y, brawler))
                click(select_x, select_y)
                print("Selected brawler", brawler)
                time.sleep(2)
                break
            else:
                print('Did not find brawler.')
            if c == 0:
                pyautogui.moveTo(520, 450)  #c
                pyautogui.mouseDown()
                time.sleep(0.3)
                pyautogui.moveTo(520, 430, duration=1)  #c
                pyautogui.mouseUp()
                c += 1
                continue  # Some weird bug causing the first frame to not get any results so this redoes it
            pyautogui.moveTo(520, 820)  #c
            pyautogui.mouseDown()
            pyautogui.moveTo(520, 490, duration=1)  #c
            pyautogui.mouseUp()
            time.sleep(1)
