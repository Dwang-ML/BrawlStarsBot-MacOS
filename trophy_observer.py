import os

import requests
from difflib import SequenceMatcher
import numpy as np
from easyocr import easyocr

from state_finder.main import crop_region
from utils import update_toml_file, load_toml_as_dict, save_dict_as_toml, api_base_url


class TrophyObserver:

    def __init__(self, brawler_list):
        self.history_file = "./cfg/match_history.toml"
        self.current_trophies = None
        self.current_mastery = None
        self.match_history = self.load_history(brawler_list)
        self.match_history['total'] = {"defeat": 0, "victory": 0, "draw": 0}
        self.sent_match_history = {brawler: {"defeat": self.match_history[brawler]["defeat"],
                                             "victory": self.match_history[brawler]["victory"],
                                             "draw": 0}
                                   for brawler in brawler_list}
        self.win_streak = 0
        self.match_counter = 0  # New counter for the number of matches
        self.trophy_lose_ranges = [(49, 0), (99, 1), (199, 2), (599, 3), (699, 4), (799, 5), (899, 6), (999, 7),
                                   (1099, 8), (1199, 11), (1299, 13), (1399, 16), (1499, 19), (1599, 22), (1699, 25), (1799, 28), (1899, 31), (1999, 34), (float("inf"), 50)]
        self.trophy_win_ranges = [(1099, 8), (1199, 7), (1299, 6), (1399, 5), (1499, 4), (1599, 3), (1699, 2), (float("inf"), 1)]
        self.mastery_win_gains = [(0, 49, 5), (50, 99, 7), (100, 149, 10), (150, 199, 12), (200, 249, 15),
                                  (250, 299, 17), (300, 349, 20), (350, 399, 23), (400, 449, 25), (450, 499, 27),
                                  (500, 549, 35), (550, 599, 40), (600, 649, 45), (650, 699, 50), (700, 749, 55),
                                  (750, 799, 60), (800, 849, 65), (850, 899, 70), (900, 949, 75), (950, 999, 80),
                                  (1000, 1049, 85), (1050, 1099, 90), (1100, 1149, 95), (1150, float('inf'), 100)]

        self.crop_region = load_toml_as_dict("./cfg/lobby_config.toml")['lobby']['trophy_observer']
        print('cr 1', crop_region)
        self.crop_region = [x * 2 for x in crop_region]
        print('cr 2', crop_region)
        self.reader = easyocr.Reader(['en'])
        self.mastery_madness_percentage = int(load_toml_as_dict("./cfg/general_config.toml")["mastery_madness"])
        self.trophies_multiplier = int(load_toml_as_dict("./cfg/general_config.toml")["trophies_multiplier"])

    @staticmethod
    def rework_game_result(res_string):
        res_string = res_string.lower()
        if res_string in ["victory", "defeat", "draw"]:
            return res_string, 1.0

        ratios = {
            "victory": SequenceMatcher(None, res_string, 'victory').ratio(),
            "defeat": SequenceMatcher(None, res_string, 'defeat').ratio(),
            "draw": SequenceMatcher(None, res_string, "draw").ratio()
        }
        highest_ratio_string = max(ratios, key=ratios.get)

        return highest_ratio_string, ratios[highest_ratio_string]

    def win_streak_gain(self):
        return min(self.win_streak - 1, 5)  # Max gain from win streak is 5

    def calc_lost_decrement(self):
        for max_trophies, loss in self.trophy_lose_ranges:
            if float(self.current_trophies) <= float(max_trophies):
                return loss

    def calc_win_increment(self):
        for max_trophies, gain in self.trophy_win_ranges:
            if float(self.current_trophies) <= float(max_trophies):
                return gain*self.trophies_multiplier + self.win_streak_gain()

    def load_history(self, brawler_list):
        loaded_data = {}
        if os.path.exists(self.history_file):
            loaded_data = load_toml_as_dict(self.history_file)
        else:
            loaded_data = {}

        # Ensure each brawler has an entry
        for brawler in brawler_list:
            if brawler not in loaded_data:
                loaded_data[brawler] = {"defeat": 0, "victory": 0, "draw": 0}

        if "total" not in loaded_data:
            loaded_data["total"] = {"defeat": 0, "victory": 0, "draw": 0}

        return loaded_data

    def save_history(self):
        save_dict_as_toml(self.match_history, self.history_file)

    def add_trophies(self, game_result, current_brawler):
        if current_brawler not in self.sent_match_history:
            self.sent_match_history[current_brawler] = {"defeat": 0, "victory": 0, "draw": 0}
        if current_brawler not in self.match_history:
            self.match_history[current_brawler] = {"defeat": 0, "victory": 0, "draw": 0}

        print(f"Found game result!: {game_result} win streak: {self.win_streak}")
        old = self.current_trophies
        if game_result == "victory":
            self.win_streak += 1
            self.current_trophies += self.calc_win_increment()
        elif game_result == "defeat":
            self.win_streak = 0
            self.current_trophies -= self.calc_lost_decrement()
        elif game_result == "draw":
            print("Nothing changed. Draw detected")

        else:
            print("Catastrophic failure")

        print(f"Trophies : {old} -> {self.current_trophies}")
        print("Current mastery points:", self.current_mastery)
        self.match_history[current_brawler][game_result] += 1
        self.match_history["total"][game_result] += 1

        self.match_counter += 1  # Increment the match counter
        if self.match_counter % 4 == 0:  # If every 4th match
            self.send_results_to_api()  # Send results to the API

        self.save_history()
        return True

    def add_mastery(self, game_result):
        if game_result == "victory":
            for min_value, max_value, gain in self.mastery_win_gains:
                if float(min_value) <= float(self.current_trophies) <= float(max_value):
                    self.current_mastery += gain * (1 + self.mastery_madness_percentage / 100)
                    return

    def find_game_result(self, screenshot, current_brawler, game_result=None):
        if not game_result:
            screenshot = screenshot.crop(self.crop_region)
            array_screenshot = np.array(screenshot)
            result = self.reader.readtext(array_screenshot)

            if len(result) == 0:
                return False

            _, text, conf = result[0]
            game_result, ratio = self.rework_game_result(text)
            if ratio < 0.5:
                print("Couldn't find game result")
                return False

        self.add_trophies(game_result, current_brawler)
        self.add_mastery(game_result)
        return True

    def change_trophies(self, new):
        print(f"Trophies changed from {self.current_trophies} to {new}")
        self.current_trophies = new

    def send_results_to_api(self):
        # Prepare the data by calculating the difference between current and sent stats
        data = {}
        for brawler, stats in self.match_history.items():
            if brawler != "total":
                if brawler not in self.sent_match_history:
                    self.sent_match_history[brawler] = {"defeat": 0, "victory": 0, "draw": 0}
                new_stats = {
                    "wins": stats["victory"] - self.sent_match_history[brawler]["victory"],
                    "defeats": stats["defeat"] - self.sent_match_history[brawler]["defeat"],
                    "draws": 0
                }
                if any(new_stats.values()):  # Only include if there are new results
                    data[brawler] = new_stats

        if not data:  # No new data to send
            return

        if api_base_url != "localhost":
            # Send the POST request
            try:
                response = requests.post(f'https://{api_base_url}/api/brawlers', json=data)
                if response.status_code == 200:
                    print("Results successfully sent to API")
                    # Update sent_match_history with the latest totals
                    for brawler, stats in self.match_history.items():
                        if brawler != "total":
                            self.sent_match_history[brawler]["victory"] = stats["victory"]
                            self.sent_match_history[brawler]["defeat"] = stats["defeat"]
                            self.sent_match_history[brawler]["draw"] = 0
                else:
                    print(f"Failed to send results to API. Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending results to API: {e}")