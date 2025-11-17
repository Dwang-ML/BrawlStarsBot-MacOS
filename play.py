import math
import random
import time

import pyautogui
from shapely import LineString
from shapely.geometry import Polygon
from state_finder.main import get_state
from detect import Detect
from state_finder.main import get_in_game_state
from utils import load_toml_as_dict, count_hsv_pixels

pyautogui.PAUSE = 0

TILE_SIZE = 70


class Movement:
    def __init__(self):
        self.fix_movement_keys = {
            "delay_to_trigger": load_toml_as_dict("cfg/bot_config.toml")["unstuck_movement_delay"],
            "duration": load_toml_as_dict("cfg/bot_config.toml")["unstuck_movement_hold_time"],
            "toggled": False,
            "started_at": time.time(),
            "fixed": ""
        }
        self.game_mode = load_toml_as_dict("cfg/bot_config.toml")["gamemode_type"]
        self.should_use_gadget = load_toml_as_dict("cfg/bot_config.toml")["bot_uses_gadgets"] == "yes" or \
                                 load_toml_as_dict("cfg/bot_config.toml")["bot_uses_gadgets"] == "true"
        self.gadget_treshold = load_toml_as_dict("cfg/time_tresholds.toml")["gadget"]
        self.hypercharge_treshold = load_toml_as_dict("cfg/time_tresholds.toml")["hypercharge"]
        self.walls_treshold = load_toml_as_dict("cfg/time_tresholds.toml")["wall_detection"]
        self.keep_walls_in_memory = self.walls_treshold <= 1
        self.last_walls_data = None
        self.keys_hold = []
        self.time_since_movement_change = time.time()
        self.time_since_gadget_checked = time.time()
        self.is_gadget_ready = False
        self.time_since_hypercharge_checked = time.time()
        self.is_hypercharge_ready = False

    @staticmethod
    def get_enemy_pos(enemy):
        return (enemy[0] + enemy[2]) / 2, (enemy[1] + enemy[3]) / 2

    @staticmethod
    def get_player_pos(player_data):
        return (player_data[0] + player_data[2]) / 2, (player_data[1] + player_data[3]) / 2

    @staticmethod
    def get_distance(enemy_coords, player_coords):
        return math.hypot(enemy_coords[0] - player_coords[0], enemy_coords[1] - player_coords[1])

    @staticmethod
    def is_there_enemy(enemy_data):
        if enemy_data is None or enemy_data[0] is None:
            return False
        return True

    @staticmethod
    def get_horizontal_move_key(direction_x, opposite=False):
        if opposite:
            return "A" if direction_x > 0 else "D"
        return "D" if direction_x > 0 else "A"

    @staticmethod
    def get_vertical_move_key(direction_y, opposite=False):
        if opposite:
            return "W" if direction_y > 0 else "S"
        return "S" if direction_y > 0 else "W"

    @staticmethod
    def attack():
        pyautogui.press("e")

    @staticmethod
    def use_hypercharge():
        pyautogui.press("h")

    @staticmethod
    def use_gadget():
        pyautogui.press("g")

    @staticmethod
    def get_random_attack_key():
        random_movement = random.choice(["A", "W", "S", "D"])
        random_movement += random.choice(["A", "W", "S", "D"])
        return random_movement

    @staticmethod
    def reverse_movement(movement):
        # Create a translation table
        movement = movement.lower()
        translation_table = str.maketrans("wasd", "sdwa")
        return movement.translate(translation_table)

    def unstuck_movement_if_needed(self, movement, current_time=time.time()):
        movement = movement.lower()
        if self.fix_movement_keys['toggled']:
            if current_time - self.fix_movement_keys['started_at'] > self.fix_movement_keys['duration']:
                self.fix_movement_keys['toggled'] = False

            return self.fix_movement_keys['fixed']

        if "".join(self.keys_hold) != movement and movement[::-1] != "".join(self.keys_hold):
            self.time_since_movement_change = current_time

        # print(f"Last change: {self.time_since_movement_change}", f" self.hold: {self.keys_hold}",f" c movement: {movement}")
        if current_time - self.time_since_movement_change > self.fix_movement_keys["delay_to_trigger"]:
            reversed_movement = self.reverse_movement(movement)

            if reversed_movement == "s":
                reversed_movement = random.choice(['aw', 'dw'])
            elif reversed_movement == "w":
                reversed_movement = random.choice(['as', 'ds'])

            """
            If reverse movement is either "w" or "s" it means the bot is stuck
            going forward or backward. This happens when it doesn't detect a wall in front
            so to go around it it could either go to the left diagonal or right
            """

            self.fix_movement_keys['fixed'] = reversed_movement
            self.fix_movement_keys['toggled'] = True
            self.fix_movement_keys['started_at'] = current_time
            print(f"REVERSED! from {movement} to {reversed_movement}!")
            return reversed_movement

        return movement


class Play(Movement):
    def __init__(self, main_info_model, specific_info_model, starting_screen_model, tile_detector_model):
        super().__init__()

        self.specific_game_data = {}
        self.Detect_main_info = Detect(main_info_model, classes=['enemy', 'player', 'teammate'])
        self.Detect_specific_info = Detect(specific_info_model,
                                           classes=['ammo', 'ball', 'damage_taken', 'defeat', 'draw',
                                                    'enemy_health_bar', 'enemy_position', 'gadget', 'gem',
                                                    'hypercharge', 'player_health_bar', 'player_position', 'respawning',
                                                    'shot_success', 'super', 'teammate_health bar', 'teammate_position',
                                                    'victory', 'wall', 'bush', '8bit', 'amber', 'ash', 'barley', 'bea',
                                                    'belle', 'bibi', 'bo', 'bonnie', 'brock', 'bull', 'buster', 'buzz',
                                                    'byron', 'carl', 'charlie', 'chester', 'chuck', 'colette', 'colt',
                                                    'cordelious', 'crow', 'darryl', 'doug', 'dynamike', 'edgar',
                                                    'primo', 'emz', 'eve', 'fang', 'frank', 'gale', 'gene', 'grom',
                                                    'gray', 'griff', 'gus', 'hank', 'jacky', 'janet', 'jessie', 'kit',
                                                    'larry_lawrie', 'leon', 'lola', 'lou', 'mandy', 'maisie', 'max',
                                                    'meg', 'melodie', 'mico', 'mortis', 'mrp', 'nani', 'nita', 'otis',
                                                    'pam', 'penny', 'piper', 'poco', 'rico', 'rosa', 'rt', 'ruffs',
                                                    'sam', 'sandy', 'shelly', 'spike', 'sprout', 'stu', 'squeak',
                                                    'surge', 'tara', 'tick', 'willow', 'lily', 'enemy_ability',
                                                    'ally_ability'])
        self.Detect_starting_screen = Detect(starting_screen_model)
        self.tile_detector_model_classes = load_toml_as_dict("cfg/bot_config.toml")["wall_model_classes"]

        self.Detect_tile_detector = Detect(
            tile_detector_model,
            classes=self.tile_detector_model_classes
        )

        self.time_since_movement = time.time()
        self.time_since_gadget_checked = time.time()
        self.time_since_hypercharge_checked = time.time()
        self.time_since_walls_checked = time.time()
        self.wait_for_random_movement = 0
        self.same_move_up_counter = {'wa': 0, 'wd': 0}
        self.last_player_coords = []
        self.time_since_movement_change = time.time()
        self.current_brawler = None
        self.is_hypercharge_ready = False
        self.is_gadget_ready = False
        self.brawler_types = {
            "throwers": ["barley", "dynamike", "grom", "larrylawrie", "mrp", "sprout", "tick", "willow"]
        }
        self.brawler_ranges = self.load_brawler_ranges()
        self.time_since_detections = {
            "player": time.time(),
            "enemy": time.time(),
        }
        self.time_since_last_proceeding = time.time()

        self.last_movement = ''
        self.last_movement_time = time.time()
        self.movement_hold_time = 0.2  # Minimum time to hold a movement before changing
        self.wall_history = []
        self.wall_history_length = 3  # Number of frames to keep walls
        self.scene_data = []
        self.should_detect_walls = load_toml_as_dict("cfg/bot_config.toml")["gamemode"] in ["brawlball", "brawl_ball",
                                                                                            "brawll ball"]
        self.minimum_movement_delay = load_toml_as_dict("cfg/bot_config.toml")["minimum_movement_delay"]
        self.no_detection_proceed_delay = load_toml_as_dict("cfg/time_tresholds.toml")["no_detection_proceed"]
        self.gadget_pixels_minimum = load_toml_as_dict("cfg/bot_config.toml")["gadget_pixels_minimum"]
        self.hypercharge_pixels_minimum = load_toml_as_dict("cfg/bot_config.toml")["hypercharge_pixels_minimum"]
        self.wall_detection_confidence = load_toml_as_dict("cfg/bot_config.toml")["wall_detection_confidence"]

    def get_specific_data(self, frame):
        self.specific_game_data = self.Detect_specific_info.detect_objects(frame)

    @staticmethod
    def load_brawler_ranges():
        ranges = load_toml_as_dict("cfg/ranges.toml")
        current_width, current_height = pyautogui.size()
        screen_size_ratio = min(current_height / 1080, current_width / 1920)
        for k, v in ranges.items():
            if k == "title":
                continue
            ranges[k] = [int(v[0] * screen_size_ratio), int(v[1] * screen_size_ratio)]
        return ranges

    @staticmethod
    def walls_are_in_line_of_sight(line_of_sight, walls):
        for wall in walls:
            x1, y1, x2, y2 = wall
            wall_polygon = Polygon([
                (x1, y1), (x2, y1),
                (x2, y2), (x1, y2)
            ])
            if line_of_sight.intersects(wall_polygon):
                return True
        return False

    def no_enemy_movement(self, player_data, walls):
        player_position = self.get_player_pos(player_data)
        preferred_movement = 'W' if self.game_mode == 3 else 'D'  # Adjust based on game mode

        if not self.is_path_blocked(player_position, preferred_movement, walls):
            return preferred_movement
        else:
            # Try alternative movements
            alternative_moves = ['W', 'A', 'D', 'S']
            alternative_moves.remove(preferred_movement)
            random.shuffle(alternative_moves)
            for move in alternative_moves:
                if not self.is_path_blocked(player_position, move, walls):
                    return move
            print("No movement possible?")
            # If no movement is possible, return empty string
            return preferred_movement

    def is_enemy_hittable(self, player_pos, enemy_pos, walls):
        if self.current_brawler in self.brawler_types['throwers']:
            return True
        if self.walls_are_in_line_of_sight(LineString([player_pos, enemy_pos]), walls):
            return False
        return True

    def find_closest_enemy(self, enemy_data, player_coords, walls):
        player_pos_x, player_pos_y = player_coords
        closest_distance = float('inf')
        closest_hittable = None
        closest_unhittable = None
        for enemy in enemy_data:
            distance = self.get_distance(self.get_enemy_pos(enemy), player_coords)
            if distance < closest_distance:
                if self.is_enemy_hittable((player_pos_x, player_pos_y), self.get_enemy_pos(enemy), walls):
                    closest_hittable = [self.get_enemy_pos(enemy), distance]
                    continue

                closest_unhittable = [self.get_enemy_pos(enemy), distance]
        if bool(closest_hittable):
            return closest_hittable
        elif bool(closest_unhittable):
            return closest_unhittable

        return None, None

    def get_main_data(self, frame):
        data = self.Detect_main_info.detect_objects(frame, conf_tresh=0.7)
        return data

    def is_path_blocked(self, player_pos, move_direction, walls, distance=TILE_SIZE):  # Increased distance
        dx, dy = 0, 0
        if 'w' in move_direction.lower():
            dy -= distance
        if 's' in move_direction.lower():
            dy += distance
        if 'a' in move_direction.lower():
            dx -= distance
        if 'd' in move_direction.lower():
            dx += distance
        new_pos = (player_pos[0] + dx, player_pos[1] + dy)
        path_line = LineString([player_pos, new_pos])
        return self.walls_are_in_line_of_sight(path_line, walls)

    @staticmethod
    def validate_game_data(data):
        incomplete = False
        if "player" not in data.keys():
            incomplete = True  # This is required so track_no_detections can also keep track if enemy is missing

        if "enemy" not in data.keys():
            data['enemy'] = None

        if 'wall' not in data.keys() or not data['wall']:
            data['wall'] = []

        return False if incomplete else data

    def track_no_detections(self, data):
        if not data:
            data = {
                "enemy": None,
                "player": None
            }
        for key, value in data.items():
            if value:
                self.time_since_detections[key] = time.time()

    def do_movement(self, movement):
        movement = movement.lower()
        keys_to_keyDown = []
        keys_to_keyUp = []
        for key in ['w', 'a', 'd', 's']:
            if key in self.keys_hold and key in movement:
                keys_to_keyDown.append(key)
                continue

            if key in movement:
                keys_to_keyDown.append(key)
                continue

            keys_to_keyUp.append(key)

        for key in keys_to_keyDown:
            pyautogui.keyDown(key)

        for key in keys_to_keyUp:
            pyautogui.keyUp(key)

        self.keys_hold = keys_to_keyDown

    def get_brawler_range(self, brawler):
        return self.brawler_ranges[brawler]

    def loop(self, brawler, data, current_time):
        safe_range, attack_range = self.get_brawler_range(brawler)
        movement = self.get_movement(player_data=data['player'][0], enemy_data=data['enemy'], safe_range=safe_range,
                                     attack_range=attack_range, walls=data['wall'])
        current_time = time.time()
        if current_time - self.time_since_movement > self.minimum_movement_delay:
            movement = self.unstuck_movement_if_needed(movement, current_time)
            self.do_movement(movement)
            self.time_since_movement = time.time()
        return movement

    def check_if_hypercharge_ready(self, frame):
        screenshot = frame.crop((1080 * 2, 810 * 2, 1150 * 2, 880 * 2))  #c
        purple_pixels = count_hsv_pixels(screenshot, (137, 158, 159), (179, 255, 255))

        if purple_pixels > self.hypercharge_pixels_minimum:
            print("Hyper charge ready", purple_pixels)
            return True
        return False

    def check_if_gadget_ready(self, frame):
        screenshot = frame.crop((1250 * 2, 810 * 2, 1320 * 2, 880 * 2))  #c
        green_pixels = count_hsv_pixels(screenshot, (57, 219, 165), (62, 255, 255))
        if green_pixels > self.gadget_pixels_minimum:
            print('Gadget ready', green_pixels)
            return True
        return False

    def get_tile_data(self, frame):
        tile_data = self.Detect_tile_detector.detect_objects(frame, conf_tresh=self.wall_detection_confidence)
        return tile_data

    def process_tile_data(self, tile_data):
        walls = []
        for class_name, boxes in tile_data.items():
            if class_name != 'bush':
                walls.extend(boxes)

        # Add walls to history
        self.wall_history.append(walls)
        if len(self.wall_history) > self.wall_history_length:
            self.wall_history.pop(0)
        # Combine walls from history
        combined_walls = self.combine_walls_from_history()

        return combined_walls

    def combine_walls_from_history(self):
        wall_counts = {}
        for walls in self.wall_history:
            for wall in walls:
                wall_key = tuple(wall)
                wall_counts[wall_key] = wall_counts.get(wall_key, 0) + 1

        threshold = 1

        combined_walls = [list(wall) for wall, count in wall_counts.items() if count >= threshold]
        print(f"Combined walls: {combined_walls}")

        return combined_walls

    def get_movement(self, player_data, enemy_data, safe_range, attack_range, walls):
        player_pos = self.get_player_pos(player_data)
        if not self.is_there_enemy(enemy_data):
            return self.no_enemy_movement(player_data, walls)
        enemy_coords, enemy_distance = self.find_closest_enemy(enemy_data, player_pos, walls)
        direction_x = enemy_coords[0] - player_pos[0]
        direction_y = enemy_coords[1] - player_pos[1]

        # Determine initial movement direction
        if enemy_distance > safe_range:  # Move towards the enemy
            move_horizontal = self.get_horizontal_move_key(direction_x)
            move_vertical = self.get_vertical_move_key(direction_y)
            state = "towards"
        else:  # Move away from the enemy
            move_horizontal = self.get_horizontal_move_key(direction_x, opposite=True)
            move_vertical = self.get_vertical_move_key(direction_y, opposite=True)
            state = "escape"

        if self.game_mode == 3:
            opposite_move = 'D' if move_horizontal == 'A' else 'A'
            movement_options = [move_horizontal + move_vertical, move_horizontal, opposite_move]
        elif self.game_mode == 5:
            opposite_move = 'W' if move_vertical == 'S' else 'S'
            movement_options = [move_horizontal + move_vertical, move_vertical, opposite_move]
        else:
            movement_options = [move_horizontal + move_vertical, move_horizontal, move_vertical]

        # Check for walls and adjust movement
        for move in movement_options:
            if not self.is_path_blocked(player_pos, move, walls):
                movement = move
                break
        else:
            print("all paths blocked")
            # If all preferred directions are blocked, try alternative directions
            alternative_moves = ['W', 'A', 'D', 'S']
            random.shuffle(alternative_moves)
            for move in alternative_moves:
                if not self.is_path_blocked(player_pos, move, walls):
                    movement = move
                    break
            else:
                movement = ''  # No movement possible

        current_time = time.time()
        if movement != self.last_movement:
            if current_time - self.last_movement_time >= self.movement_hold_time:
                self.last_movement = movement
                self.last_movement_time = current_time
            else:
                movement = self.last_movement  # Continue previous movement
        else:
            self.last_movement_time = current_time  # Reset timer if movement didn't change

        # Attack if enemy is within attack range and hittable
        if enemy_distance <= attack_range:
            if self.should_use_gadget == True and self.is_gadget_ready:
                self.use_gadget()
                self.time_since_gadget_checked = time.time()
                self.is_gadget_ready = False
            if self.is_hypercharge_ready:
                self.use_hypercharge()
                self.time_since_hypercharge_checked = time.time()
                self.is_hypercharge_ready = False
            enemy_hittable = self.is_enemy_hittable(player_pos, enemy_coords, walls)
            print("enemy hittable", enemy_hittable, "enemy_distance", enemy_distance)
            if enemy_hittable:
                self.attack()

        return movement

    def main(self, frame, brawler):
        current_time = time.time()
        data = self.get_main_data(frame)
        print("Main data detected:", data)
        if self.should_detect_walls and current_time - self.time_since_walls_checked > self.walls_treshold:

            tile_data = self.get_tile_data(frame)

            walls = self.process_tile_data(tile_data)

            self.time_since_walls_checked = current_time
            self.last_walls_data = walls
            data['wall'] = walls
        elif self.keep_walls_in_memory:
            data['wall'] = self.last_walls_data

        data = self.validate_game_data(data)
        self.track_no_detections(data)
        if not data:
            self.time_since_movement_change = time.time()
            for key in ['w', 'a', 'd', 's']:
                pyautogui.keyUp(key)
            self.keys_hold = []
            if current_time - self.time_since_last_proceeding > self.no_detection_proceed_delay:
                current_state = get_state(frame)
                if current_state != "match":
                    self.time_since_last_proceeding = current_time
                else:
                    print("Haven't detected the player in a while - proceeding")
                    pyautogui.press("q")
                    self.time_since_last_proceeding = time.time()
            return
        self.time_since_last_proceeding = time.time()
        self.is_hypercharge_ready = False
        if current_time - self.time_since_hypercharge_checked > self.hypercharge_treshold:
            self.is_hypercharge_ready = self.check_if_hypercharge_ready(frame)
            self.time_since_hypercharge_checked = current_time
        self.is_gadget_ready = False
        if current_time - self.time_since_gadget_checked > self.gadget_treshold:
            self.is_gadget_ready = self.check_if_gadget_ready(frame)
            self.time_since_gadget_checked = current_time

        movement = self.loop(brawler, data, current_time)

        if data:
            # Record scene data
            self.scene_data.append({
                'frame_number': len(self.scene_data),
                'player': data.get('player', []),
                'enemy': data.get('enemy', []),
                'wall': data.get('wall', []),
                'movement': movement,
            })
            self.generate_visualization()

    def generate_visualization(self, output_filename='visualization.mp4'):
        import cv2
        import numpy as np

        frame_size = (1920, 1080)  # Adjust as needed
        fps = 10

        # Initialize VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_filename, fourcc, fps, frame_size)

        for frame_data in self.scene_data:
            # Create a blank image
            img = np.zeros((frame_size[1], frame_size[0], 3), np.uint8)

            # Scale factors if needed
            scale_x = frame_size[0] / 1920
            scale_y = frame_size[1] / 1080

            if frame_data['wall']:
                # Draw walls
                for wall in frame_data['wall']:
                    x1, y1, x2, y2 = map(int, wall)
                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (128, 128, 128), -1)  # Gray walls

            if frame_data['enemy']:
                # Draw enemies
                for enemy in frame_data['enemy']:
                    x1, y1, x2, y2 = map(int, enemy)
                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), -1)  # Red enemies

            if frame_data['player']:
                # Draw player
                for player in frame_data['player']:
                    x1, y1, x2, y2 = map(int, player)
                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), -1)  # Green player

            # Draw movement decision
            movement = frame_data['movement']
            direction = self.movement_to_direction(movement)
            cv2.putText(img, f'Movement: {direction}', (10, frame_size[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 255), 1)

            # Write frame to video
            out.write(img)

        print('Visualization generated.')
        out.release()

    @staticmethod
    def movement_to_direction(movement):
        mapping = {
            'w': 'up',
            'a': 'left',
            's': 'down',
            'd': 'right',
            'wa': 'up-left',
            'aw': 'up-left',
            'wd': 'up-right',
            'dw': 'up-right',
            'sa': 'down-left',
            'as': 'down-left',
            'sd': 'down-right',
            'ds': 'down-right',
        }
        movement = movement.lower()
        movement = ''.join(sorted(movement))
        return mapping.get(movement, 'idle' if movement == '' else movement)
