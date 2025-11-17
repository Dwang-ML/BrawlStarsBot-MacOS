import hashlib
import io
import os
from io import BytesIO
from pynput.mouse import Controller, Button
import json
import aiohttp
import requests
import toml
from PIL import Image
from discord import Webhook
import discord
from easyocr import easyocr
import cv2
import numpy as np
from PIL import Image
from packaging import version
import mss
import time

reader = easyocr.Reader(['en'])  # Assuming English text, you can modify the list to include other languages.

mouse = Controller()
api_base_url = "localhost"


def extract_text_and_positions(image_path):
    results = reader.readtext(image_path)
    text_details = {}
    for (bbox, text, prob) in results:
        top_left, top_right, bottom_right, bottom_left = bbox
        cx = (top_left[0] + top_right[0] + bottom_right[0] + bottom_left[0]) / 4
        cy = (top_left[1] + top_right[1] + bottom_right[1] + bottom_left[1]) / 4
        center = (cx, cy)
        formatted_bbox = {
            'top_left': top_left,
            'top_right': top_right,
            'bottom_right': bottom_right,
            'bottom_left': bottom_left,
            'center': center
        }

        text_details[text.lower()] = formatted_bbox

    return text_details


class ScreenshotTaker:
    def __init__(self):
        self.sct = mss.mss()

    def take(self):
        image = None
        while image is None:
            try:
                sct_img = self.sct.grab(self.sct.monitors[0])
                image = Image.fromarray(np.array(sct_img))
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
                image = None
        return image


def count_hsv_pixels(pil_image, low_hsv, high_hsv):
    opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    hsv_image = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, np.array(low_hsv), np.array(high_hsv))
    pixel_count = np.count_nonzero(mask)
    return pixel_count


def save_brawler_data(data):
    """
    Save the given data to a json file. As a list of dictionaries.
    """
    with open("latest_brawler_data.json", 'w') as f:
        json.dump(data, f, indent=4)


def find_template_center(main_img, template):
    main_image_cv = cv2.cvtColor(np.array(main_img), cv2.COLOR_RGB2GRAY)
    template_cv = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2GRAY)
    w, h = template_cv.shape[::-1]

    # Perform template matching
    result = cv2.matchTemplate(main_image_cv, template_cv, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if the match is found based on a threshold value
    threshold = 0.8
    if max_val >= threshold:
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(main_image_cv, top_left, bottom_right, 255, 2)  # White rectangle with thickness 2

        return center_x, center_y
    else:
        return False


def load_toml_as_dict(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return toml.load(f)
    else:
        return {}


def save_dict_as_toml(data, file_path):
    with open(file_path, 'w') as f:
        toml.dump(data, f)


def update_toml_file(path, new_data):
    with open(path, 'w') as file:
        toml.dump(new_data, file)


def get_brawler_list():
    if api_base_url == "localhost":
        return ['8bit', 'amber', 'angelo', 'ash', 'barley', 'bea', 'belle', 'berry', 'bibi', 'bo', 'bonnie',
                'brock', 'bull', 'buster', 'buzz', 'byron', 'carl', 'charlie', 'chester', 'chuck', 'clancy',
                'colette', 'colt', 'cordelius', 'crow', 'darryl', 'doug', 'draco', 'dynamike', 'edgar',
                'elprimo', 'emz', 'eve', 'fang', 'frank', 'gale', 'gene', 'gray', 'griff', 'grom', 'gus',
                'hank', 'jacky', 'janet', 'jessie', 'kit', 'larrylawrie', 'leon', 'lily', 'lola', 'lou',
                'maisie', 'mandy', 'max', 'meg', 'melodie', 'mico', 'mortis', 'mrp', 'nani', 'nita', 'otis',
                'pam', 'pearl', 'penny', 'piper', 'poco', 'rt', 'rico', 'rosa', 'ruffs', 'sam', 'sandy',
                'shelly', 'spike', 'sprout', 'squeak', 'stu', 'surge', 'tara', 'tick', 'willow', 'moe', 'kenji', "juju",
                "shade", "ollie", "meeple", "finx", "lumi", "kaze", "jaeyong", "alli"]
    url = f'https://{api_base_url}/get_brawler_list'
    response = requests.post(url)
    if response.status_code == 201:
        data = response.json()
        return data.get('brawlers', [])
    else:
        return []


def update_missing_brawler_ranges(brawlers):
    brawler_ranges = load_toml_as_dict("cfg/ranges.toml")
    for brawler in brawlers:
        if brawler not in brawler_ranges:
            # Fetch the range from the API
            range_values = get_brawler_range(brawler)
            if range_values:
                brawler_ranges[brawler] = range_values
                # Save the updated ranges to the TOML file
                save_dict_as_toml(brawler_ranges, "cfg/ranges.toml")
                print(f"Added range for brawler '{brawler}': {range_values}")
                # Download the brawler icon
                save_brawler_icon(brawler)
            else:
                print(f"Could not find range for brawler '{brawler}'")
        if not os.path.exists(f"./api/assets/brawler_icons/{brawler}.png"):
            save_brawler_icon(brawler)


def get_brawler_range(brawler_name):
    url = f'https://{api_base_url}/get_brawler_range'  # Adjust the URL if necessary
    response = requests.post(url, json={'brawler_name': brawler_name})
    if response.status_code == 200:
        data = response.json()
        return data.get('range', [])
    else:
        print(f"Error fetching range for '{brawler_name}': {response.status_code} - {response.text}")
        return None


def save_brawler_icon(brawler_name):
    # Clean the brawler name for filename
    brawler_name_clean = brawler_name.lower().replace(' ', '').replace('-', '').replace('.', '').replace('&',
                                                                                                         '')
    brawlers_url = "https://api.brawlapi.com/v1/brawlers"
    response = requests.get(brawlers_url)
    if response.status_code != 200:
        print(f"Failed to fetch brawlers from API: {response.status_code}")
        return
    brawlers_data = response.json()['list']

    # Find the brawler in the API data
    for brawler_obj in brawlers_data:
        api_brawler_name = brawler_obj['name'].lower().replace(' ', '').replace('-', '').replace('.',
                                                                                                 '').replace(
            '&', '')
        if api_brawler_name == brawler_name_clean:
            icon_url = brawler_obj['imageUrl2']
            img_response = requests.get(icon_url)
            if img_response.status_code == 200:
                image = Image.open(BytesIO(img_response.content))
                image.save(f"api/assets/brawler_icons/{brawler_name_clean}.png")
                print(f"Saved icon for brawler '{brawler_name}'")
            else:
                print(f"Failed to download icon for '{brawler_name}'")
            return
    print(f"Icon not found for brawler '{brawler_name}'")


def update_icons():
    icons = ['brawl_stars_icon.png', 'brawl_stars_icon_big.png']
    base_url = f'https://{api_base_url}/get_icon/'
    for icon_name in icons:
        icon_url = base_url + icon_name
        response = requests.get(icon_url)
        if response.status_code == 200:
            with open(f'./state_finder/images_to_detect/{icon_name}', 'wb') as f:
                f.write(response.content)
            print(f"Downloaded and updated {icon_name}")
        else:
            print(f"Failed to download {icon_name}. Status code: {response.status_code}")


def click(x, y):
    x = int(x)
    y = int(y)
    mouse.position = (x, y)
    mouse.click(Button.left, 1)


def get_latest_version():
    url = f'https://{api_base_url}/check_version'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('version', '')
    else:
        return None


def check_version():
    if api_base_url != "localhost":
        latest_version = get_latest_version()
        if latest_version:
            current_version = load_toml_as_dict("cfg/general_config.toml").get('pyla_version', '')
            if version.parse(current_version) < version.parse(latest_version):
                print(
                    f"Warning: (ignore if you're using early access) You are not using the latest public version of Pyla. \nCheck the discord for the latest download link.")
        else:
            print(
                "Error, couldn't get the version, please check your internet connection or go ask for help in the discord.")


async def async_notify_user(message_type: str | None = None, screenshot: Image = None) -> None:
    user_id = load_toml_as_dict("cfg/general_config.toml")["discord_id"]
    webhook_url = load_toml_as_dict("cfg/general_config.toml")["personal_webhook"]
    if not webhook_url:
        print("Couldn't notify: no webhook configured.")
        return

    if message_type == "completed":
        status_line = f"Pyla has completed all its targets!"
        ping = f"<@{user_id}>"
    elif message_type == "bot_is_stuck":
        status_line = f"Your bot is currently stuck!"
        ping = f"<@{user_id}>"
    else:
        status_line = f"Pyla completed brawler goal for {message_type}!"
        ping = f"<@{user_id}>"

    buffer = io.BytesIO()
    screenshot.save(buffer, format="PNG")
    buffer.seek(0)
    file = discord.File(buffer, filename="screenshot.png")

    # Build the embed that holds both the text and the screenshot
    embed = discord.Embed(description=status_line)
    embed.set_image(url="attachment://screenshot.png")  # show the attached screenshot

    # Send the embed
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        print("sending webhook")
        await webhook.send(embed=embed, file=file, username="Pyla notifier", content=ping)


def get_discord_link():
    if api_base_url == "localhost":
        return "https://discord.gg/xUusk3fw4A"
    url = f'https://{api_base_url}/get_discord_link'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('link', '')
    else:
        return None


def get_online_wall_model_hash():
    url = f'https://{api_base_url}/get_wall_model_hash'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('hash', '')
    else:
        return None


def calculate_sha256(file_path):
    """
    Calculate the SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file:
        # Read the file in chunks to handle large files
        for chunk in iter(lambda: file.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def current_wall_model_is_latest() -> bool:
    """
    Check if the current wall model is the latest version.
    """
    local_hash = calculate_sha256("models/tileDetector.onnx")
    online_hash = get_online_wall_model_hash()
    return local_hash == online_hash


def get_latest_wall_model_file():
    #download the new model to replace the current file and also updates the tile list
    url = f'https://{api_base_url}/get_wall_model_file'
    response = requests.get(url)
    if response.status_code == 200:
        with open("./models/tileDetector.onnx", "wb") as file:
            file.write(response.content)
        print("Downloaded the latest wall model.")
    else:
        print(f"Failed to download the latest wall model. Status code: {response.status_code}")


def get_latest_wall_model_classes():
    url = f'https://{api_base_url}/get_wall_model_classes'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('classes', [])
    else:
        return None


def update_wall_model_classes():
    classes = get_latest_wall_model_classes()
    current_classes = load_toml_as_dict("cfg/bot_config.toml")["wall_model_classes"]
    if classes:
        if classes != current_classes:
            print("New wall model classes found. Updating...")
            update_toml_file("cfg/bot_config.toml", {"wall_model_classes": classes})
            print("Updated the wall model classes.")
    else:
        print("Failed to update the wall model classes, please report this error.")


def cprint(text: str, hex_color: str):  #omg color!!!
    try:
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        print(f"\033[38;2;{r};{g};{b}m{text}\033[0m")
    except Exception:
        print(text)
