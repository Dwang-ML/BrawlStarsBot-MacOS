import os
import sys

import utils
from utils import api_base_url

sys.path.append(os.path.abspath('../'))


class App:
    def __init__(self, login_page, select_brawler_page, pyla_main, brawlers, hub_menu):
        self.login = login_page
        self.select_brawler = select_brawler_page
        self.logged_in = False
        self.brawler_data = None
        self.pyla_main = pyla_main
        self.brawlers = brawlers
        self.hub_menu = hub_menu

    def set_is_logged(self, value):
        self.logged_in = value

    def set_data(self, value):
        self.brawler_data = value

    def start(self, capture_thread, pyla_version, get_latest_version):
        self.login(self.set_is_logged)
        if self.logged_in:
            if api_base_url == "localhost":
                self.hub_menu(pyla_version, pyla_version)
            else:
                self.hub_menu(pyla_version, get_latest_version())
            self.select_brawler(self.set_data, self.brawlers)
            if self.brawler_data:
                capture_thread.start()
                utils.save_brawler_data(self.brawler_data)
                self.pyla_main(self.brawler_data)

