import json
import tkinter as tk
from math import ceil

import customtkinter as ctk
import pyautogui
from PIL import Image
from customtkinter import CTkImage
from utils import load_toml_as_dict
from tkinter import filedialog

debug = load_toml_as_dict("./cfg/general_config.toml")['super_debug'] == "yes"
width, height = pyautogui.size()
pyla_version = load_toml_as_dict("./cfg/general_config.toml")['pyla_version']


class SelectBrawler:
    def __init__(self, data_setter, brawlers):
        self.app = ctk.CTk()

        square_size = 50
        amount_of_rows = ceil(len(brawlers) / 10) + 1
        necessary_height = (145 + amount_of_rows * square_size + (amount_of_rows - 1) * 3)
        self.app.title(f"PylaAI v{pyla_version}")
        self.brawlers = brawlers

        self.app.geometry(f"{str(600)}x{necessary_height}+{str(600)}")
        self.data_setter = data_setter
        self.colors = {
            'gray': "#7d7777",
            'red': "#cd5c5c",
            'darker_white': '#c4c4c4',
            'dark gray': '#1c1c1c',
            'cherry red': '#960a00',
            'ui box gray': '#242424',
            'chess white': '#f0d9b5',
            'chess brown': '#b58863',
            'indian red': "#cd5c5c"
        }

        self.app.configure(fg_color=self.colors['ui box gray'])

        self.images = []
        self.brawlers_data = []
        self.farm_type = ""

        for brawler in self.brawlers:
            img_path = f"./api/assets/brawler_icons/{brawler}.png"
            img = Image.open(img_path)

            img_tk = CTkImage(img, size=(square_size, square_size))
            self.images.append((brawler, img_tk))  # Store tuple of brawler name and image

        # Entry widget for filtering
        self.filter_var = tk.StringVar()
        self.filter_entry = ctk.CTkEntry(
            self.app, textvariable=self.filter_var,
            placeholder_text="Type brawler name...", font=("", 20), width=200, fg_color=self.colors['ui box gray'], border_color=self.colors['cherry red'], text_color="white"
        )
        ctk.CTkLabel(self.app, text="Search Brawler", font=("Comic sans MS", 20),
                     text_color=self.colors['cherry red']).place(x=203, y=20)
        self.filter_entry.place(x=170, y=52)
        self.filter_var.trace_add("write", lambda *args: self.update_images(self.filter_var.get()))

        # Frame to hold the images
        self.image_frame = ctk.CTkFrame(self.app, fg_color=self.colors['ui box gray'])
        self.image_frame.place(x=0, y=100)

        self.update_images("")
        ctk.CTkButton(self.app, text="Start", command=self.start_bot, fg_color=self.colors['ui box gray'],
                      text_color="white",
                      font=("Comic sans MS", 25), border_color=self.colors['cherry red'],
                      border_width=2).place(x=450, y=(necessary_height - 60))

        ctk.CTkButton(self.app, text="Load Brawler Config", command=self.load_brawler_config,
                      fg_color=self.colors['ui box gray'],
                      text_color="white",
                      font=("Comic sans MS", 25), border_color=self.colors['cherry red'],
                      border_width=2).place(x=10, y=(necessary_height - 60))
        self.app.mainloop()

    def set_farm_type(self, value):
        self.farm_type = value

    def start_bot(self):
        self.data_setter(self.brawlers_data)
        self.app.destroy()

    def load_brawler_config(self):
        # open file select dialog to select a json file
        file_path = filedialog.askopenfilename(
            title="Select Brawler Config File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    brawlers_data = json.load(file)
                    try:
                        brawlers_data[0]['push_until']
                        for brawler_data in brawlers_data:
                            # if we find a brawler that has already reached it's goal, we remove it from the list
                            push_type = brawler_data["type"]
                            if brawler_data["push_until"] <= brawler_data[push_type]:
                                brawlers_data.remove(brawler_data)
                        self.brawlers_data = brawlers_data
                        print("Brawler data loaded successfully.")
                    except Exception as e:
                        print("Invalid data format. Expected a list of brawler data.", e)
            except Exception as e:
                print(f"Error loading brawler data: {e}")

    def on_image_click(self, brawler):
        self.open_brawler_entry(brawler)

    def open_brawler_entry(self, brawler):
        top = ctk.CTkToplevel(self.app)
        top.configure(fg_color=self.colors['ui box gray'])
        top.geometry(
            f"{str(300)}x{str(450)}+{str(1100)}+{str(200)}")
        top.title("Enter Brawler Data")
        top.attributes("-topmost", True)

        push_until_var = tk.StringVar()
        push_until_entry = ctk.CTkEntry(
            top, textvariable=push_until_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=2, height=28
        )

        trophies_var = tk.StringVar()
        trophies_entry = ctk.CTkEntry(
            top, textvariable=trophies_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=2, height=28
        )

        mastery_var = tk.StringVar()
        mastery_entry = ctk.CTkEntry(
            top, textvariable=mastery_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=2, height=28
        )

        current_win_streak_var = tk.StringVar(value="0")  # Set the default value to "0"
        current_win_streak_entry = ctk.CTkEntry(
            top, textvariable=current_win_streak_var, fg_color=self.colors['ui box gray'], text_color="white",
            border_color=self.colors['cherry red'], border_width=2, height=28
        )

        auto_pick_var = tk.BooleanVar(value=True)  # Checkbox variable, ticked by default
        auto_pick_checkbox = ctk.CTkCheckBox(
            top, text="Auto-pick Brawler in game", variable=auto_pick_var,
            fg_color=self.colors['cherry red'], text_color="white", checkbox_height=24
        )

        def submit_data():
            push_until_value = push_until_var.get()
            push_until_value = int(push_until_value) if push_until_value.isdigit() else ""
            trophies_value = int(trophies_var.get())
            mastery_value = mastery_var.get()
            mastery_value = int(mastery_value) if mastery_value.isdigit() else ""
            current_win_streak_value = current_win_streak_var.get()
            if self.farm_type == "trophies" and mastery_value == "":
                mastery_value = 0
            data = {
                "brawler": brawler,
                "push_until": push_until_value,
                "trophies": trophies_value,
                "mastery": mastery_value,
                "type": self.farm_type,
                "automatically_pick": auto_pick_var.get(),
                "win_streak": int(current_win_streak_value)
            }

            if data["type"] == "":
                if data["trophies"] <= data["mastery"]:
                    data["type"] = "trophies"
                else:
                    data["type"] = "mastery"

            self.brawlers_data = [item for item in self.brawlers_data if item["brawler"] != data["brawler"]]
            self.brawlers_data.append(data)

            print("Selected Brawler Data :", self.brawlers_data)
            top.destroy()

        submit_button = ctk.CTkButton(
            top, text="Submit", command=submit_data, fg_color=self.colors['ui box gray'],
            border_color=self.colors['cherry red'],
            text_color="white", border_width=2, width=80
        )

        farm_type_button_frame = ctk.CTkFrame(top, width=200, height=50,
                                              fg_color=self.colors['ui box gray'])

        self.mastery_button = ctk.CTkButton(farm_type_button_frame, text="Mastery", width=85,
                                            command=lambda: self.set_farm_type_color("mastery"),
                                            hover_color=self.colors['cherry red'],
                                            font=("", 15),
                                            fg_color=self.colors["ui box gray"],
                                            border_color=self.colors['cherry red'],
                                            border_width=2
                                            )
        self.trophies_button = ctk.CTkButton(farm_type_button_frame, text="Trophies", width=85,
                                             command=lambda: self.set_farm_type_color("trophies"),
                                             hover_color=self.colors['cherry red'],
                                             font=("", 15),
                                             fg_color=self.colors["ui box gray"],
                                             border_color=self.colors['cherry red'], border_width=2
                                             )

        self.trophies_button.place(x=10)
        self.mastery_button.place(x=110)

        ctk.CTkLabel(top, text=f"Brawler: {brawler}", font=("Comic sans MS", 20),
                     text_color=self.colors['red']).pack(
            pady=7)
        farm_type_button_frame.pack()
        ctk.CTkLabel(top, text="Push Until", font=("Comic sans MS", 15),
                     text_color=self.colors['chess white']).pack()
        push_until_entry.pack(pady=4)
        ctk.CTkLabel(top, text="Trophies", font=("Comic sans MS", 15),
                     text_color=self.colors['chess white']).pack()
        trophies_entry.pack(pady=4)
        ctk.CTkLabel(top, text="Mastery", font=("Comic sans MS", 15),
                     text_color=self.colors['chess white']).pack()
        mastery_entry.pack(pady=4)
        ctk.CTkLabel(top, text="Brawler's Win Streak", font=("Comic sans MS", 15),
                     text_color=self.colors['chess white']).pack()
        current_win_streak_entry.pack(pady=4)
        auto_pick_checkbox.pack(pady=4)  # Add the checkbox to the UI
        submit_button.pack(pady=7)

    def set_farm_type_color(self, value):
        self.farm_type = value
        if value == "mastery":
            self.mastery_button.configure(fg_color=self.colors['cherry red'])
            self.trophies_button.configure(fg_color=self.colors['ui box gray'])
        else:
            self.mastery_button.configure(fg_color=self.colors['ui box gray'])
            self.trophies_button.configure(fg_color=self.colors['cherry red'])

    def update_images(self, filter_text):
        for widget in self.image_frame.winfo_children():
            widget.destroy()

        row_num = 0
        col_num = 0

        for brawler, img_tk in self.images:
            if brawler.startswith(filter_text.lower()):
                label = ctk.CTkLabel(self.image_frame, image=img_tk, text="")
                label.bind("<Button-1>", lambda e, b=brawler: self.on_image_click(b))  # Bind click event
                label.grid(row=row_num, column=col_num, padx=5, pady=3)

                col_num += 1
                if col_num == 10:  # Move to the next row after 10 columns
                    col_num = 0
                    row_num += 1


def dummy_data_setter(data):
    print("Data set:", data)
