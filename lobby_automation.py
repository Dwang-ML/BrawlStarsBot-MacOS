import time
from utils import cprint, linebreak
from easyocr import easyocr
from queue import Empty

import numpy as np
import pyautogui
from utils import click
from utils import extract_text_and_positions, ScreenshotTaker, scroll_up

reader = easyocr.Reader(['en'])


class LobbyAutomation:
    def __init__(self, frame_queue):
        self.Screenshot = ScreenshotTaker()
        self.frame_queue = frame_queue

    @staticmethod
    def check_for_idle(frame):
        linebreak()
        # Process screenshot and crop for faster detection time
        screenshot = frame
        w, h = screenshot.size

        # Proportional crop for consistency across devices
        left_pct = 0.2
        top_pct = 0.33
        right_pct = 0.8
        bottom_pct = 0.66

        # Convert to pixel coordinates
        left = int(w * left_pct)
        top = int(h * top_pct)
        right = int(w * right_pct)
        bottom = int(h * bottom_pct)

        # Crop
        screenshot = screenshot.crop((left, top, right, bottom))

        # OCR
        text = extract_text_and_positions(np.array(screenshot))

        # Check for idle
        idle_state = 'idle disconnect' in text.keys()
        if idle_state:
            if 'reload' in text.keys():
                x, y = 420 + int(text['reload']['center'][0]) // 2, 400 + int(text['reload']['center'][1]) // 2
                cprint('Idle detected. Clicking ({}, {}) to RELOAD from idle disconnect.'.format(x, y), 'ACTION')
                click(x, y)
                return
            else:
                cprint('Idle detected. Couldn\'t find RELOAD button, proceeding.', 'ACTION')
                return
        cprint('User is not idle.', 'INFO')

        # Check for disconnect
        dc_state = 'connection lost' in text.keys()
        if dc_state:
            if 'retry login' in text.keys():
                x, y = 420 + int(text['retry login']['center'][0]) // 2, 400 + int(
                    text['retry login']['center'][1]) // 2
                cprint('Disconnect detected. Clicking ({}, {}) to RETRY LOGIN from disconnect.'.format(x, y), 'ACTION')
                for _ in range(5):
                    click(x, y)
                    time.sleep(0.1)
                return
            else:
                cprint('Disconnect detected. Couldn\'t find RETRY LOGIN button, proceeding.', 'ACTION')
                return
        cprint('User is not disconnected.', 'INFO')
        linebreak()

    def select_brawler(self, brawler):
        linebreak()
        cprint('SELECTING BRAWLER', 'INFO')

        click(111, 493)  # Click brawlers button
        time.sleep(3)

        # Find brawler
        for i in range(50):
            try:
                screenshot = self.frame_queue.get(timeout=1)
                if screenshot is None:
                    raise Empty
            except Empty:
                continue

            screenshot = screenshot.resize((int(screenshot.width * 0.65), int(screenshot.height * 0.65)))
            screenshot = np.array(screenshot)
            cprint('Extracting text on current screen...', 'ACTION')
            results = extract_text_and_positions(screenshot)
            reworked_results = {}
            for key in results.keys():
                orig_key = key
                for symbol in [' ', '-', '.', '&']:
                    key = key.replace(symbol, '')
                replace_dict = {
                    'shey': 'shelly',
                    '@ola': 'lola',
                    '@eon': 'leon',
                    'rzco': 'rico',
                }
                if key in replace_dict:
                    key = replace_dict[key]
                reworked_results[key] = results[orig_key]
            if brawler in reworked_results.keys():
                # Click brawler
                cprint('Found brawler ' + brawler + '.', 'CHECK')
                x, y = reworked_results[brawler]['center']
                x, y = x // 0.65, y // 0.65  # Rescale back
                cprint('Clicking ({}, {}) to {}\' brawler page.'.format(x, y, brawler), 'ACTION')
                click(x, y)  # Clicking the brawler
                time.sleep(2)
                click(269, 976)  # Clicking select button
                cprint('Selected brawler ' + brawler + '.', 'CHECK')
                time.sleep(3)
                break
            else:
                cprint('Did not find brawler.', 'FAIL')
            scroll_up(705, 841, 709, 519, 300)
            linebreak()
            time.sleep(1)
