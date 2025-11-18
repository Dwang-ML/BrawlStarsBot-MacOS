import time
from easyocr import easyocr
from queue import Empty

import numpy as np
import pyautogui
from utils import click
from utils import extract_text_and_positions, ScreenshotTaker, load_toml_as_dict

reader = easyocr.Reader(['en'])


class LobbyAutomation:
    def __init__(self, frame_queue):
        self.Screenshot = ScreenshotTaker()
        self.frame_queue = frame_queue

    @staticmethod
    def check_for_idle(frame):
        # Process screenshot and crop for faster detection time
        screenshot = frame
        screenshot = screenshot.crop((420 * 2, 400 * 2, 1050 * 2, 580 * 2))
        text = extract_text_and_positions(np.array(screenshot))

        # Check for idle
        idle_state = 'idle disconnect' in text.keys()
        if idle_state:
            if 'reload' in text.keys():
                x, y = 420 + int(text['reload']['center'][0]) // 2, 400 + int(text['reload']['center'][1]) // 2
                print('Idle detected. Clicking ({}, {}) to RELOAD from idle disconnect.'.format(x, y))
                click(x, y)
                return
            else:
                print('Idle detected. Couldn\'t find RELOAD button, proceeding.')
                return
        print('User is not idle.')

        # Check for disconnect
        dc_state = 'connection lost' in text.keys()
        if dc_state:
            if 'retry login' in text.keys():
                x, y = 420 + int(text['retry login']['center'][0]) // 2, 400 + int(
                    text['retry login']['center'][1]) // 2
                print('Disconnect detected. Clicking ({}, {}) to RETRY LOGIN from disconnect.'.format(x, y))
                for _ in range(5):
                    click(x, y)
                    time.sleep(0.1)
                return
            else:
                print('Disconnect detected. Couldn\'t find RETRY LOGIN button, proceeding.')
                return
        print('User is not disconnected.')

    def select_brawler(self, brawler):
        print('Selecting brawler.')

        # Retrieve screenshot
        print('Waiting for screenshot...')
        ss_text = []
        while True:
            time.sleep(0.5)

            # Retrieve screenshot
            screenshot = self.frame_queue.get(timeout=1)
            screenshot = screenshot.resize((int(screenshot.width * 0.65), int(screenshot.height * 0.65)))
            if screenshot == Empty: continue

            # Check if BRAWLER button is found
            ss_text = reader.readtext(np.array(screenshot))
            for item in ss_text:
                text = item[1].lower()
                if "brawlers" in text:
                    break
            else:
                continue
            break
        print('Screenshot received.')

        # Retrieve and click
        x = 0
        y = 0
        for (bbox, text, conf) in ss_text:
            if 'brawlers' in text.lower():
                # bbox format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                x = sum(xs) / 4
                y = sum(ys) / 4
                break
        x = x // 0.65 // 2
        y = y // 0.65 // 2
        print('Clicking ({}, {}) for brawler selection button.'.format(x, y))
        click(x, y)

        # Find brawler
        for i in range(50):
            try:
                screenshot = self.frame_queue.get(timeout=1)
            except Empty:
                continue

            screenshot = screenshot.resize((int(screenshot.width * 0.65), int(screenshot.height * 0.65)))
            screenshot = np.array(screenshot)
            print('Extracting text on current screen...')
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
            print('All detected text while looking for brawler name:', reworked_results.keys())
            if brawler in reworked_results.keys():
                # Click brawler
                print('Found brawler', brawler)
                x, y = reworked_results[brawler]['center']
                x, y = x // 0.65 // 2, y // 0.65 // 2  # Rescale back and divide due to Mac system
                print('Clicking ({}, {}) to confirm {}.'.format(x, y, brawler))
                click(x, y)
                time.sleep(2)

                # Retrieve screenshot
                print('Waiting for screenshot...')
                ss_text = []
                while True:
                    time.sleep(0.5)

                    # Retrieve screenshot
                    screenshot = self.frame_queue.get(timeout=1)
                    screenshot = screenshot.resize((int(screenshot.width * 0.65), int(screenshot.height * 0.65)))
                    if screenshot == Empty: continue

                    # Check if SELECT button is found
                    ss_text = reader.readtext(np.array(screenshot))
                    for item in ss_text:
                        text = item[1].lower()
                        if text == 'selegt':
                            text = 'select'
                        if "select" in text:
                            break
                    else:
                        continue
                    break
                print('Screenshot received.')

                # Retrieve and click
                x = 0
                y = 0
                for (bbox, text, conf) in ss_text:
                    if ('select' in text.lower()) or ('selegt' in text.lower()):
                        # bbox format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                        xs = [p[0] for p in bbox]
                        ys = [p[1] for p in bbox]
                        x = sum(xs) / 4
                        y = sum(ys) / 4
                        break
                x = x // 0.65 // 2
                y = y // 0.65 // 2
                print('Clicking ({}, {}) to select {}'.format(x, y, brawler))
                click(x, y)
                print('Selected brawler', brawler)
                time.sleep(5)
                break
            else:
                print('Did not find brawler.')
            pyautogui.scroll(-100)
            time.sleep(1)
