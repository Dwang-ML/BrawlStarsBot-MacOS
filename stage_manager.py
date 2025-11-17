import os.path

import asyncio
import time
from queue import Empty

import cv2
import numpy as np
import pyautogui
import requests

from lobby_automation import LobbyAutomation
from state_finder.main import get_state
from trophy_observer import TrophyObserver
from utils import find_template_center, extract_text_and_positions, load_toml_as_dict, async_notify_user, \
    save_brawler_data

user_id = load_toml_as_dict("cfg/general_config.toml")['discord_id']
debug = load_toml_as_dict("cfg/general_config.toml")['super_debug'] == "yes"
user_webhook = load_toml_as_dict("cfg/general_config.toml")['personal_webhook']


def notify_user(message_type):
    # message type will be used to have conditions determining the message
    # but for now there's only one possible type of message
    message_data = {
        'content': f"<@{user_id}> Pyla Bot has completed all it's targets !"
    }

    response = requests.post(user_webhook, json=message_data)

    if response.status_code != 204:
        print(
            f'Failed to send message. Be sure to have put a valid webhook url in the config. Status code: {response.status_code}')


orig_screen_width, orig_screen_height = 1920, 1080
width, height = pyautogui.size()
width_ratio = width / orig_screen_width
height_ratio = height / orig_screen_height
scale_factor = min(width_ratio, height_ratio)


def load_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    orig_height, orig_width = image.shape[:2]

    # Calculate the new dimensions based on the scale factor
    new_width = int(orig_width * scale_factor)
    new_height = int(orig_height * scale_factor)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image


class StageManager:
    def __init__(self, screenshot_taker, brawlers_data, frame_queue):
        self.Screenshot = screenshot_taker
        self.states = {
            'shop': self.quit_shop,
            'brawler_selection': self.quit_shop,
            'popup': self.close_pop_up,
            'match': lambda: 0,
            'end': self.end_game,
            'lobby': self.start_game,
            'play_store': self.click_brawl_stars,
            "brawl_stars_crashed": self.start_brawl_stars,
            'star_drop': self.click_star_drop
        }
        self.Lobby_automation = LobbyAutomation(frame_queue)
        self.lobby_config = load_toml_as_dict("./cfg/lobby_config.toml")
        self.brawl_stars_icon = load_image("state_finder/images_to_detect/brawl_stars_icon.png")
        self.brawl_stars_icon_big = load_image("state_finder/images_to_detect/brawl_stars_icon_big.png")
        self.mastery_points_icon = load_image("./state_finder/images_to_detect/mastery_points.PNG")
        self.close_popup_icon = load_image("state_finder/images_to_detect/close_popup.png")
        self.brawlers_pick_data = brawlers_data
        brawler_list = [brawler["brawler"] for brawler in brawlers_data]
        self.Trophy_observer = TrophyObserver(brawler_list)
        self.time_since_last_stat_change = time.time()
        self.frame_queue = frame_queue
        self.long_press_star_drop = load_toml_as_dict("./cfg/general_config.toml")["long_press_star_drop"]

    def start_brawl_stars(self, frame):
        data = extract_text_and_positions(np.array(frame))
        for key in list(data.keys()):
            if key.replace(" ", "") in ["brawl", "brawlstars", "stars"]:
                x, y = data[key]['center']
                pyautogui.click(x, y)
                return

        x, y = self.lobby_config['lobby']['brawl_stars_icon'][0] * width_ratio, \
               self.lobby_config['lobby']['brawl_stars_icon'][1] * height_ratio
        pyautogui.click(x, y)

    @staticmethod
    def validate_trophies(trophies_string):
        trophies_string = trophies_string.lower()
        while "s" in trophies_string:
            trophies_string = trophies_string.replace("s", "5")
        numbers = ''.join(filter(str.isdigit, trophies_string))

        if not numbers:
            return False

        trophy_value = int(numbers)
        return trophy_value

    def start_game(self, data):
        values = {
            "trophies": self.Trophy_observer.current_trophies,
            "mastery": self.Trophy_observer.current_mastery
        }

        type_of_push = self.brawlers_pick_data[0]['type']
        value = values[type_of_push]
        if value == "" and type_of_push == "mastery":
            value = -99999
        push_current_brawler_till = self.brawlers_pick_data[0]['push_until']
        if push_current_brawler_till == "" and type_of_push == "mastery":
            push_current_brawler_till = 99999

        if value >= push_current_brawler_till:
            if len(self.brawlers_pick_data) <= 1:
                print("Brawler reached required trophies/mastery. No more brawlers selected for pushing in the menu. "
                      "Bot will"
                      "now pause itself until closed.", value, push_current_brawler_till)
                time.sleep(10 ** 5)
                loop = asyncio.new_event_loop()
                screenshot = self.Screenshot.take()
                loop.run_until_complete(async_notify_user("bot_is_stuck", screenshot))
                loop.close()
                return
            loop = asyncio.new_event_loop()
            screenshot = self.Screenshot.take()
            loop.run_until_complete(async_notify_user(self.brawlers_pick_data[0]["brawler"], screenshot))
            loop.close()
            self.brawlers_pick_data.pop(0)
            self.Trophy_observer.change_trophies(self.brawlers_pick_data[0]['trophies'])
            self.Trophy_observer.current_mastery = self.brawlers_pick_data[0]['mastery'] if self.brawlers_pick_data[0][
                                                                                                'mastery'] != "" else -99999
            self.Trophy_observer.win_streak = self.brawlers_pick_data[0]['win_streak']
            next_brawler_name = self.brawlers_pick_data[0]['brawler']
            if self.brawlers_pick_data[0]["automatically_pick"]:
                print("Picking next automatically picked brawler.")
                try:
                    screenshot = self.frame_queue.get(timeout=1)
                except Empty:
                    screenshot = self.Screenshot.take()
                current_state = get_state(screenshot)
                if current_state != "lobby":
                    print("Trying to reach the lobby to switch brawler")

                while current_state != "lobby":
                    pyautogui.press("q")
                    print("Pressed Q to return to lobby")
                    time.sleep(1)
                self.Lobby_automation.select_brawler(next_brawler_name)
            else:
                print("Next brawler is in manual mode, waiting 10 seconds to let user switch.")

        # q btn is over the start btn
        pyautogui.press("q")
        print("Pressed Q to start a match")

    def click_brawl_stars(self, frame):
        screenshot = frame.crop((50, 4, 900, 31))
        detection = find_template_center(screenshot, self.brawl_stars_icon)
        if detection:
            x, y = detection
            pyautogui.click(x=x + 50, y=y)

    def click_star_drop(self):
        if self.long_press_star_drop == "yes":
            pyautogui.keyDown("q")
            time.sleep(10)
            pyautogui.keyUp("q")
        else:
            pyautogui.press("q")

    def end_game(self):
        screenshot = self.Screenshot.take()

        found_game_result = False
        current_state = get_state(screenshot)
        while current_state == "end":
            if not found_game_result and time.time() - self.time_since_last_stat_change > 10:

                # will return True if updates trophies, trophies are updated inside Trophy observer
                found_game_result = self.Trophy_observer.find_game_result(screenshot,
                                                                          current_brawler=self.brawlers_pick_data[0][
                                                                              'brawler'])
                self.time_since_last_stat_change = time.time()
                values = {
                    "trophies": self.Trophy_observer.current_trophies,
                    "mastery": self.Trophy_observer.current_mastery
                }
                type_to_push = self.brawlers_pick_data[0]['type']
                value = values[type_to_push]
                self.brawlers_pick_data[0][type_to_push] = value
                save_brawler_data(self.brawlers_pick_data)
                push_current_brawler_till = self.brawlers_pick_data[0]['push_until']

                # things so to have mastery be farmed infinitely if no initial or target mastery value are set
                if value == "" and type_to_push == "mastery":
                    value = -99999
                if push_current_brawler_till == "" and type_to_push == "mastery":
                    push_current_brawler_till = 99999

                if value >= push_current_brawler_till:
                    if len(self.brawlers_pick_data) <= 1:
                        print(
                            "Brawler reached required trophies/mastery. No more brawlers selected for pushing in the menu. "
                            "Bot will"
                            "now pause itself until closed.")
                        loop = asyncio.new_event_loop()
                        screenshot = self.Screenshot.take()
                        loop.run_until_complete(async_notify_user("completed", screenshot))
                        loop.close()
                        if os.path.exists("latest_brawler_data.json"):
                            os.remove("latest_brawler_data.json")
                        time.sleep(10 ** 5)
                        return
            pyautogui.press("q")
            print("Game has ended, pressing Q")
            time.sleep(3)
            screenshot = self.Screenshot.take()
            current_state = get_state(screenshot)
        print("Game has ended", current_state)

    @staticmethod
    def quit_shop():
        pyautogui.click(100, 60)

    @staticmethod
    def click_coords(coords, in_between=None):
        for coord in coords:
            pyautogui.click(coord)

            if in_between:
                pyautogui.click(in_between)

    def close_pop_up(self):
        screenshot = self.Screenshot.take()
        popup_location = find_template_center(screenshot, self.close_popup_icon)
        if popup_location:
            pyautogui.click(popup_location)

    def do_state(self, state, data=None):
        if data:
            self.states[state](data)
            return
        self.states[state]()
