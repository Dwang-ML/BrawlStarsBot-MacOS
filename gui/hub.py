import sys

import customtkinter as ctk
import webbrowser
import os
import time
import pyautogui
from PIL import Image
import tkinter as tk
import mss
from utils import load_toml_as_dict, save_dict_as_toml, get_discord_link

orig_screen_width, orig_screen_height = 1920, 1080
width, height = pyautogui.size()
width_ratio = width / orig_screen_width
height_ratio = height / orig_screen_height
scale_factor = min(width_ratio, height_ratio)
monitors = [str(i) for i in range(1, len(mss.mss().monitors))]


def S(value):
    """Helper to scale integer sizes based on the user's screen."""
    return int(value * scale_factor)


class Hub:
    """
    Updated, more user-friendly interface for the Pyla bot.
    """

    def __init__(self,
                 version_str,
                 latest_version_str,
                 correct_zoom=True,
                 on_close_callback=None):

        self.version_str = version_str
        self.latest_version_str = latest_version_str
        self.correct_zoom = correct_zoom
        self.on_close_callback = on_close_callback

        # -----------------------------------------------------------------------------------------
        # Load configs
        # -----------------------------------------------------------------------------------------
        self.bot_config_path = "cfg/bot_config.toml"
        self.time_tresholds_path = "cfg/time_tresholds.toml"
        self.match_history_path = "cfg/match_history.toml"
        self.general_config_path = "cfg/general_config.toml"

        self.bot_config = load_toml_as_dict(self.bot_config_path)
        self.time_tresholds = load_toml_as_dict(self.time_tresholds_path)
        self.match_history = load_toml_as_dict(self.match_history_path)
        self.general_config = load_toml_as_dict(self.general_config_path)

        # -----------------------------------------------------------------------------------------
        # Defaults
        # -----------------------------------------------------------------------------------------
        # Bot config defaults
        self.bot_config.setdefault("gamemode_type", 3)
        self.bot_config.setdefault("gamemode", "brawlball")
        self.bot_config.setdefault("bot_uses_gadgets", "yes")
        self.bot_config.setdefault("minimum_movement_delay", 0.4)

        # Time thresholds defaults
        self.time_tresholds.setdefault("state_check", 5)
        self.time_tresholds.setdefault("no_detections", 10)
        self.time_tresholds.setdefault("idle", 10)
        self.time_tresholds.setdefault("specific_brawlers", 999)
        self.time_tresholds.setdefault("gadget", 0.5)
        self.time_tresholds.setdefault("hypercharge", 3)

        # General config defaults
        self.general_config.setdefault("check_if_brawl_stars_crashed", "yes")
        self.general_config.setdefault("max_ips", "auto")
        self.general_config.setdefault("super_debug", "yes")
        self.general_config.setdefault("cpu_or_gpu", "auto")
        self.general_config.setdefault("monitor", "0")
        self.general_config.setdefault("mastery_madness", "0")
        self.general_config.setdefault("long_press_star_drop", "no")
        self.general_config.setdefault("trophies_multiplier", 1.0)
        self.general_config.setdefault("run_for_minutes", 0)

        # -----------------------------------------------------------------------------------------
        # Appearance
        # -----------------------------------------------------------------------------------------
        ctk.set_appearance_mode("dark")

        # -----------------------------------------------------------------------------------------
        # Main window
        # -----------------------------------------------------------------------------------------
        self.app = ctk.CTk()
        self.app.title(f"Pyla Hub – {self.version_str}")
        self.app.geometry(f"{S(1000)}x{S(750)}")
        self.app.resizable(False, False)

        # For showing tooltips in Toplevel windows
        self.tooltip_window = None

        # -----------------------------------------------------------------------------------------
        # Main TabView
        # -----------------------------------------------------------------------------------------
        self.tabview = ctk.CTkTabview(
            self.app,
            width=S(980),
            height=S(640),
            corner_radius=S(10)
        )
        self.tabview.pack(pady=S(10), padx=S(10), fill="x", expand=False)

        # Enlarge the segmented tab buttons
        self.tabview._segmented_button.configure(
            corner_radius=S(10),
            border_width=2,
            fg_color="#4A4A4A",
            selected_color="#AA2A2A",
            selected_hover_color="#BB3A3A",
            unselected_color="#333333",
            unselected_hover_color="#555555",
            text_color="#FFFFFF",
            font=("Arial", S(16), "bold"),
            height=S(40)
        )

        # Add tabs
        self.tab_overview = self.tabview.add("Overview")
        self.tab_additional = self.tabview.add("Additional Settings")
        self.tab_timers = self.tabview.add("Timers")
        self.tab_history = self.tabview.add("Match History")

        # Init each tab
        self._init_overview_tab()
        self._init_additional_tab()
        self._init_timers_tab()
        self._init_history_tab()

        # Main loop
        self.app.mainloop()

    # ---------------------------------------------------------------------------------------------
    #  Tooltip Handler
    # ---------------------------------------------------------------------------------------------
    def attach_tooltip(self, widget, text):
        """Attach a tooltip to a widget by creating a small Toplevel on hover,
        and ensure it gets destroyed as soon as the mouse leaves (even quickly).
        """

        def show_tooltip(event):
            # Destroy any tooltip that might already exist
            hide_tooltip(None)

            # Create a small Toplevel for the tooltip
            self.tooltip_window = ctk.CTkToplevel(self.app)
            self.tooltip_window.overrideredirect(True)
            self.tooltip_window.attributes("-topmost", True)

            # Position near the cursor
            x = event.x_root + 10
            y = event.y_root + 10
            self.tooltip_window.geometry(f"+{x}+{y}")

            # Label inside the Toplevel
            label = ctk.CTkLabel(
                self.tooltip_window,
                text=text,
                fg_color="#333333",
                text_color="#FFFFFF",
                corner_radius=S(6),
                font=("Arial", S(12))
            )
            label.pack(padx=S(5), pady=S(3))

            #  If mouse enters the tooltip window itself, destroy the tooltip.
            #  This prevents "orphaned" tooltips if the mouse quickly jumps
            #  from the label onto the tooltip.
            self.tooltip_window.bind("<Enter>", hide_tooltip)

        def hide_tooltip(_):
            if self.tooltip_window is not None:
                self.tooltip_window.destroy()
                self.tooltip_window = None

        # Bind to label’s <Enter> and <Leave>
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    # ---------------------------------------------------------------------------------------------
    #  Overview Tab
    # ---------------------------------------------------------------------------------------------
    def _init_overview_tab(self):
        frame = self.tab_overview

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(expand=True, fill="both")

        row_ = 0

        # -----------------------------------------------------------------
        # 1) Warnings at the top (bigger, red), if any
        # -----------------------------------------------------------------
        w_list = []
        if not self.correct_zoom:
            w_list.append("Warning: Your Windows zoom isn't 100% (DPI != 96).")
        if self.latest_version_str and self.version_str != self.latest_version_str:
            w_list.append(f"Warning: You are not on the latest version ({self.latest_version_str}).")

        if w_list:
            warn_text = "\n".join(w_list)
            warn_label = ctk.CTkLabel(
                container,
                text=warn_text,
                text_color="#e74c3c",
                font=("Arial", S(16), "bold")
            )
            warn_label.grid(row=row_, column=0, columnspan=2, pady=S(10))
            row_ += 1

        # -----------------------------------------------------------------
        # 2) Map Orientation selection
        # -----------------------------------------------------------------
        self.gamemode_type_var = tk.IntVar(value=self.bot_config["gamemode_type"])

        orientation_frame = ctk.CTkFrame(container, fg_color="transparent")
        orientation_frame.grid(row=row_, column=0, columnspan=2, pady=S(10))

        label_type = ctk.CTkLabel(
            orientation_frame,
            text="Map Orientation:",
            font=("Arial", S(20), "bold")
        )
        label_type.pack(side="left", padx=S(15))

        def set_gamemode_type(t):
            """Only change the local var & refresh everything so frames swap."""
            self.gamemode_type_var.set(t)
            self._refresh_gamemode_buttons()

        self.btn_type_vertical = ctk.CTkButton(
            orientation_frame,
            text="Vertical",
            command=lambda: set_gamemode_type(3),
            font=("Arial", S(16), "bold"),
            corner_radius=S(6),
            width=S(120),
            height=S(40)
        )
        self.btn_type_vertical.pack(side="left", padx=S(10))

        self.btn_type_horizontal = ctk.CTkButton(
            orientation_frame,
            text="Horizontal",
            command=lambda: set_gamemode_type(5),
            font=("Arial", S(16), "bold"),
            corner_radius=S(6),
            width=S(120),
            height=S(40)
        )
        self.btn_type_horizontal.pack(side="left", padx=S(10))

        row_ += 1

        # -----------------------------------------------------------------
        # 3) Gamemode Selection as rectangular buttons
        # -----------------------------------------------------------------
        gm_label = ctk.CTkLabel(container, text="Select Gamemode:", font=("Arial", S(20), "bold"))
        gm_label.grid(row=row_, column=0, columnspan=2, pady=S(10))
        row_ += 1

        gm_buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        gm_buttons_frame.grid(row=row_, column=0, columnspan=2, pady=S(10))

        self.gm3_frame = ctk.CTkFrame(gm_buttons_frame, fg_color="transparent")
        self.gm5_frame = ctk.CTkFrame(gm_buttons_frame, fg_color="transparent")

        self.gamemode_var = tk.StringVar(value=self.bot_config["gamemode"])

        def create_gamemode_button(parent, gm_value, text_display, disabled=False, orientation=3):
            """Creates a rectangular toggle button for a gamemode."""

            def on_click():
                if disabled:
                    return
                # Set orientation + gamemode in config
                self.bot_config["gamemode_type"] = orientation
                self.bot_config["gamemode"] = gm_value
                save_dict_as_toml(self.bot_config, self.bot_config_path)

                self.gamemode_type_var.set(orientation)
                self.gamemode_var.set(gm_value)
                self._refresh_gamemode_buttons()

            btn = ctk.CTkButton(
                parent,
                text=text_display,
                command=on_click,
                corner_radius=S(6),
                width=S(150),
                height=S(40),
                font=("Arial", S(16), "bold"),
                state=("disabled" if disabled else "normal")
            )
            return btn

        # For type=3 (vertical)
        self.rb_brawlball_3 = create_gamemode_button(
            self.gm3_frame, "brawlball", "Brawlball", orientation=3
        )
        self.rb_showdown_3 = create_gamemode_button(
            self.gm3_frame, "showdown", "Showdown (Disabled)", disabled=True, orientation=3
        )
        self.rb_other_3 = create_gamemode_button(
            self.gm3_frame, "other", "Other", orientation=3
        )

        self.rb_brawlball_3.grid(row=0, column=0, padx=S(10), pady=S(5))
        self.rb_showdown_3.grid(row=0, column=1, padx=S(10), pady=S(5))
        self.rb_other_3.grid(row=0, column=2, padx=S(10), pady=S(5))

        # For type=5 (horizontal)
        self.rb_basketbrawl_5 = create_gamemode_button(
            self.gm5_frame, "basketbrawl", "Basket Brawl", orientation=5
        )
        self.rb_bb5v5_5 = create_gamemode_button(
            self.gm5_frame, "brawlball_5v5", "Brawlball 5v5", orientation=5
        )

        self.rb_basketbrawl_5.grid(row=0, column=0, padx=S(10), pady=S(5))
        self.rb_bb5v5_5.grid(row=0, column=1, padx=S(10), pady=S(5))

        def refresh_gm_buttons():
            """Refresh button colors to highlight the currently selected gamemode."""
            gm_now = self.gamemode_var.get()

            def set_button_color(btn, val):
                if val == gm_now:
                    btn.configure(fg_color="#AA2A2A", hover_color="#BB3A3A")
                else:
                    btn.configure(fg_color="#333333", hover_color="#BB3A3A")

            # For vertical set
            set_button_color(self.rb_brawlball_3, "brawlball")
            set_button_color(self.rb_showdown_3, "showdown")
            set_button_color(self.rb_other_3, "other")

            # For horizontal set
            set_button_color(self.rb_basketbrawl_5, "basketbrawl")
            set_button_color(self.rb_bb5v5_5, "brawlball_5v5")

        def refresh_orientation_buttons():
            """Refresh the orientation buttons' color based on self.gamemode_type_var."""
            t = self.gamemode_type_var.get()
            if t == 3:
                self.btn_type_vertical.configure(fg_color="#AA2A2A", hover_color="#BB3A3A")
                self.btn_type_horizontal.configure(fg_color="#333333", hover_color="#BB3A3A")
            else:
                self.btn_type_vertical.configure(fg_color="#333333", hover_color="#BB3A3A")
                self.btn_type_horizontal.configure(fg_color="#AA2A2A", hover_color="#BB3A3A")

        self._refresh_orientation_buttons = refresh_orientation_buttons

        def _refresh_gm_frames():
            """Show/hide frames depending on orientation."""
            self.gm3_frame.pack_forget()
            self.gm5_frame.pack_forget()

            if self.gamemode_type_var.get() == 3:
                self.gm3_frame.pack(side="top")
            else:
                self.gm5_frame.pack(side="top")

        def full_refresh():
            self._refresh_orientation_buttons()
            _refresh_gm_frames()
            refresh_gm_buttons()

        self._refresh_gamemode_buttons = full_refresh
        full_refresh()

        row_ += 1

        # -----------------------------------------------------------------
        # 4) Emulator Selection (3 rectangular buttons)
        # -----------------------------------------------------------------
        emulator_label = ctk.CTkLabel(container, text="Select Emulator:", font=("Arial", S(20), "bold"))
        emulator_label.grid(row=row_, column=0, columnspan=2, pady=S(10))
        row_ += 1

        self.emulator_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.emulator_frame.grid(row=row_, column=0, columnspan=2, pady=S(10))
        row_ += 1

        self.emu_var = tk.StringVar(value="BlueStacks")  # default

        def handle_emulator_choice(choice):
            self.emu_var.set(choice)
            self.general_config["check_if_brawl_stars_crashed"] = "no"
            save_dict_as_toml(self.general_config, self.general_config_path)
            refresh_emu_buttons()

        def create_emu_button(parent, text_display):
            def on_click():
                handle_emulator_choice(text_display)

            btn = ctk.CTkButton(
                parent,
                text=text_display,
                command=on_click,
                corner_radius=S(6),
                width=S(150),
                height=S(40),
                font=("Arial", S(16), "bold")
            )
            return btn

        self.btn_bluestacks = create_emu_button(self.emulator_frame, "BlueStacks")
        self.btn_others = create_emu_button(self.emulator_frame, "Others")

        self.btn_bluestacks.grid(row=0, column=1, padx=S(10), pady=S(5))
        self.btn_others.grid(row=0, column=2, padx=S(10), pady=S(5))

        def refresh_emu_buttons():
            curr_emu = self.emu_var.get()

            def color(btn, val):
                if val == curr_emu:
                    btn.configure(fg_color="#AA2A2A", hover_color="#BB3A3A")
                else:
                    btn.configure(fg_color="#333333", hover_color="#BB3A3A")

            color(self.btn_bluestacks, "BlueStacks")
            color(self.btn_others, "Others")

        refresh_emu_buttons()

        # -----------------------------------------------------------------
        # Some spacing
        # -----------------------------------------------------------------
        row_ += 1

        # -----------------------------------------------------------------
        # 5) Start Button
        # -----------------------------------------------------------------
        start_button = ctk.CTkButton(
            container,
            text="Start",
            fg_color="#c0392b",
            hover_color="#e74c3c",
            font=("Arial", S(24), "bold"),
            command=self._on_start,
            width=S(220),
            height=S(60)
        )
        start_button.grid(row=row_, column=0, columnspan=2, padx=S(20), pady=S(30))
        row_ += 1

        # -----------------------------------------------------------------
        # 6) "Pyla is free..." label at bottom, link in blue only
        # -----------------------------------------------------------------
        disclaim_frame = ctk.CTkFrame(container, fg_color="transparent")
        disclaim_frame.grid(row=row_, column=0, columnspan=2, pady=S(10))

        disclaim_label = ctk.CTkLabel(
            disclaim_frame,
            text="Pyla is free and public. Join the Discord -> ",
            font=("Arial", S(16), "bold"),
            text_color="#FFFFFF"
        )
        disclaim_label.pack(side="left")

        discord_link = get_discord_link()

        def open_discord_link():
            webbrowser.open(discord_link)

        link_label = ctk.CTkLabel(
            disclaim_frame,
            text=discord_link,
            font=("Arial", S(16), "bold"),
            text_color="#3498db",
            cursor="hand2"
        )
        link_label.pack(side="left")
        link_label.bind("<Button-1>", lambda e: open_discord_link())

        row_ += 1

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

    # ---------------------------------------------------------------------------------------------
    #  Additional Settings Tab
    # ---------------------------------------------------------------------------------------------
    def _init_additional_tab(self):
        frame = self.tab_additional
        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(expand=True, fill="both")

        # Extra space to avoid tooltip clipping
        container.grid_rowconfigure(0, minsize=S(70))

        row_idx = 1

        # -----------------------------------------------------------------------------------------
        # Helper to create labeled entries in either bot_config or general_config
        # -----------------------------------------------------------------------------------------
        def create_labeled_entry(label_text,
                                 config_key,
                                 convert_func,
                                 use_general_config=False,
                                 tooltip_text=None):
            nonlocal row_idx
            lbl = ctk.CTkLabel(container, text=label_text, font=("Arial", S(18)))
            lbl.grid(row=row_idx, column=0, sticky="e", padx=S(20), pady=S(10))

            # Decide which dictionary to read/write
            if use_general_config:
                current_config = self.general_config
                current_path = self.general_config_path
            else:
                current_config = self.bot_config
                current_path = self.bot_config_path
            var_str = tk.StringVar(value=str(current_config[config_key]))

            def on_save(*_):
                val_str = var_str.get().strip()
                if val_str == "":
                    var_str.set(str(current_config[config_key]))
                    return
                try:
                    val = convert_func(val_str)
                    current_config[config_key] = val
                    save_dict_as_toml(current_config, current_path)
                except ValueError:
                    var_str.set(str(current_config[config_key]))

            entry = ctk.CTkEntry(
                container, textvariable=var_str, width=S(120), font=("Arial", S(16))
            )
            entry.grid(row=row_idx, column=1, sticky="w", padx=S(20), pady=S(10))
            entry.bind("<FocusOut>", on_save)
            entry.bind("<Return>", on_save)

            if tooltip_text:
                self.attach_tooltip(entry, tooltip_text)

            row_idx += 1

        # 6) Minimum Movement Delay (bot_config)
        create_labeled_entry(
            label_text="Minimum Movement Delay:",
            config_key="minimum_movement_delay",
            convert_func=float,
            use_general_config=False,
            tooltip_text="How long (in seconds) the bot must maintain a movement before changing it."
        )

        # 9) Wall Detection Confidence (bot_config)
        create_labeled_entry(
            label_text="Wall Detection Confidence:",
            config_key="wall_detection_confidence",
            convert_func=float,
            use_general_config=False,
            tooltip_text="On a scale between 0 and 1, how sure must the bot be to detect a wall  (lower means it can detect more things but increases false detections and mistakes)."
        )

        # 7) Unstuck Movement Delay (bot_config)
        create_labeled_entry(
            label_text="Unstuck Movement Delay:",
            config_key="unstuck_movement_delay",
            convert_func=float,
            use_general_config=False,
            tooltip_text="How long (in seconds) can the bot maintain a movement before trying to unstuck itself."
        )

        # 8) Unstucking Duration (bot_config)
        create_labeled_entry(
            label_text="Unstucking Duration:",
            config_key="unstuck_movement_hold_time",
            convert_func=float,
            use_general_config=False,
            tooltip_text="For how long (in seconds) will the bot try to go in a different position to unstuck itself before going back to normal."
        )

        create_labeled_entry(
            label_text="Mastery Madness % amount:",
            config_key="mastery_madness",
            convert_func=int,
            use_general_config=True,
            tooltip_text="Enter the number but not the % of the current mastery madness. (for example : 300 for 300%)"
        )

        create_labeled_entry(
            label_text="Trophies Multiplier:",
            config_key="trophies_multiplier",
            convert_func=int,
            use_general_config=True,
            tooltip_text="Enter the multiplier for trophies gained per match (for example : 2 for brawl arena)."
        )

        create_labeled_entry(
            label_text="Run for (in minutes):",
            config_key="run_for_minutes",
            convert_func=int,
            use_general_config=True,
            tooltip_text="Set how many minutes the bot should run before stopping automatically. (0 means infinite)"
        )

        lbl_monitor = ctk.CTkLabel(container, text="Monitor (0=primary)", font=("Arial", S(18)))
        lbl_monitor.grid(row=row_idx, column=0, sticky="e", padx=S(20), pady=S(10))

        monitor_values = monitors
        monitor_var = tk.StringVar(value=self.general_config["monitor"])

        def on_monitor_change(choice):
            self.general_config["monitor"] = choice
            save_dict_as_toml(self.general_config, self.general_config_path)

        monitor_menu = ctk.CTkOptionMenu(
            container,
            values=monitor_values,
            command=on_monitor_change,
            variable=monitor_var,
            font=("Arial", S(16)),
            fg_color="#AA2A2A",
            button_color="#AA2A2A",
            button_hover_color="#BB3A3A",
            width=S(100),
            height=S(35)
        )
        monitor_menu.grid(row=row_idx, column=1, padx=S(20), pady=S(10), sticky="w")
        row_idx += 1

        # 4) CPU/GPU (store in general_config)
        lbl_gpu = ctk.CTkLabel(container, text="Use GPU (CPU/Auto):", font=("Arial", S(18)))
        lbl_gpu.grid(row=row_idx, column=0, sticky="e", padx=S(20), pady=S(10))

        gpu_values = ["cpu", "auto"]
        gpu_var = tk.StringVar(value=self.general_config["cpu_or_gpu"])

        def on_gpu_change(choice):
            self.general_config["cpu_or_gpu"] = choice
            save_dict_as_toml(self.general_config, self.general_config_path)

        gpu_menu = ctk.CTkOptionMenu(
            container,
            values=gpu_values,
            command=on_gpu_change,
            variable=gpu_var,
            font=("Arial", S(16)),
            fg_color="#AA2A2A",
            button_color="#AA2A2A",
            button_hover_color="#BB3A3A",
            width=S(100),
            height=S(35)
        )
        gpu_menu.grid(row=row_idx, column=1, padx=S(20), pady=S(10), sticky="w")
        row_idx += 1

        lbl_long_press = ctk.CTkLabel(container, text="Longpress star_drop:", font=("Arial", S(18)))
        lbl_long_press.grid(row=row_idx, column=0, sticky="e", padx=S(20), pady=S(10))
        long_press_var = tk.BooleanVar(
            value=(str(self.general_config["long_press_star_drop"]).lower() in ["yes", "true"])
        )

        def toggle_long_press_detection():
            self.general_config["long_press_star_drop"] = "yes" if long_press_var.get() else "no"
            save_dict_as_toml(self.general_config, self.general_config_path)

        long_press_cb = ctk.CTkCheckBox(
            container,
            text="",
            variable=long_press_var,
            command=toggle_long_press_detection,
            fg_color="#AA2A2A",
            hover_color="#BB3A3A",
            width=S(30),
            height=S(30)
        )
        long_press_cb.grid(row=row_idx, column=1, sticky="w", padx=S(20), pady=S(10))
        row_idx += 1

        # 5) Brawl Stars Crash Detection (store in general_config)
        lbl_crash = ctk.CTkLabel(container, text="Brawl Stars Crash Detection:", font=("Arial", S(18)))
        lbl_crash.grid(row=row_idx, column=0, sticky="e", padx=S(20), pady=S(10))
        crash_var = tk.BooleanVar(
            value=(str(self.general_config["check_if_brawl_stars_crashed"]).lower() in ["yes", "true"])
        )

        def toggle_crash_detection():
            self.general_config["check_if_brawl_stars_crashed"] = "yes" if crash_var.get() else "no"
            save_dict_as_toml(self.general_config, self.general_config_path)

        crash_cb = ctk.CTkCheckBox(
            container,
            text="",
            variable=crash_var,
            command=toggle_crash_detection,
            fg_color="#AA2A2A",
            hover_color="#BB3A3A",
            width=S(30),
            height=S(30)
        )
        crash_cb.grid(row=row_idx, column=1, sticky="w", padx=S(20), pady=S(10))
        row_idx += 1

        # 10) Gadget Detection Pixel Threshold (bot_config)
        create_labeled_entry(
            label_text="Gadget Detection Pixel Treshold:",
            config_key="gadget_pixels_minimum",
            convert_func=float,
            use_general_config=False,
            tooltip_text='Amount of "green" pixels the bot must detect to consider a gadget is ready.'
        )

        # 11) Hypercharge Detection Pixel Threshold (bot_config)
        create_labeled_entry(
            label_text="Hypercharge Detection Pixel Treshold:",
            config_key="hypercharge_pixels_minimum",
            convert_func=float,
            use_general_config=False,
            tooltip_text='Amount of "purple" pixels the bot must detect to consider a hypercharge is ready.'
        )

        # 3) Console Debug (store in general_config)
        lbl_debug = ctk.CTkLabel(container, text="Console Debug:", font=("Arial", S(18)))
        lbl_debug.grid(row=row_idx, column=0, sticky="e", padx=S(20), pady=S(10))
        debug_var = tk.BooleanVar(
            value=(str(self.general_config["super_debug"]).lower() in ["yes", "true"])
        )

        def toggle_debug():
            self.general_config["super_debug"] = "yes" if debug_var.get() else "no"
            save_dict_as_toml(self.general_config, self.general_config_path)

        debug_cb = ctk.CTkCheckBox(
            container,
            text="",
            variable=debug_var,
            command=toggle_debug,
            fg_color="#AA2A2A",
            hover_color="#BB3A3A",
            width=S(30),
            height=S(30)
        )
        debug_cb.grid(row=row_idx, column=1, sticky="w", padx=S(20), pady=S(10))
        row_idx += 1

        # 1) Max IPS (store in general_config)
        create_labeled_entry(
            label_text="Max IPS:",
            config_key="max_ips",
            convert_func=lambda s: s if s.lower() == "auto" else int(s),
            use_general_config=True,
            tooltip_text="Maximum Images per second the bot processes. 'auto' means no limit."
        )

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

    # ---------------------------------------------------------------------------------------------
    #  Timers Tab
    # ---------------------------------------------------------------------------------------------
    def _init_timers_tab(self):
        frame = self.tab_timers
        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.pack(expand=True, fill="both")

        container.grid_rowconfigure(0, minsize=S(70))  # extra top space for tooltips

        row_idx = 1

        def create_timer_setting(param_name, label_text, tooltip_text=None, disabled=False):
            nonlocal row_idx

            lbl = ctk.CTkLabel(container, text=label_text, font=("Arial", S(18)))
            lbl.grid(row=row_idx, column=0, padx=S(20), pady=S(10), sticky="e")

            # Frame to hold slider & entry side by side
            slider_entry_frame = ctk.CTkFrame(container, fg_color="transparent")
            slider_entry_frame.grid(row=row_idx, column=1, padx=S(20), pady=S(10), sticky="w")

            val_var = tk.StringVar(value=str(self.time_tresholds[param_name]))

            # The slider
            sld = ctk.CTkSlider(
                slider_entry_frame,
                from_=0.1,
                to=10,
                number_of_steps=99,
                width=S(200),
                command=lambda v: on_slider_change(v, val_var, param_name),
                state=("disabled" if disabled else "normal")
            )
            sld.pack(side="left", padx=S(5))

            # The text entry
            entry = ctk.CTkEntry(
                slider_entry_frame,
                textvariable=val_var,
                width=S(80),
                font=("Arial", S(16)),
                state=("disabled" if disabled else "normal")
            )
            entry.pack(side="left", padx=S(10))

            def on_save(_):
                if disabled:
                    return
                new_val_str = val_var.get().strip()
                if new_val_str == "":
                    val_var.set(str(self.time_tresholds[param_name]))
                    return
                try:
                    val = float(new_val_str)
                    self.time_tresholds[param_name] = val
                    save_dict_as_toml(self.time_tresholds, self.time_tresholds_path)
                    # Update slider visually
                    if val < 0.1:
                        sld.set(0.1)
                    elif val > 10:
                        sld.set(10)
                    else:
                        sld.set(val)
                except ValueError:
                    val_var.set(str(self.time_tresholds[param_name]))

            entry.bind("<FocusOut>", on_save)
            entry.bind("<Return>", on_save)

            def on_slider_change(value, v_var, p_name):
                if disabled:
                    return
                v = float(value)
                # update entry text
                v_var.set(f"{v:.2f}")
                self.time_tresholds[p_name] = v
                save_dict_as_toml(self.time_tresholds, self.time_tresholds_path)

            # Initialize slider
            try:
                init_val = float(self.time_tresholds[param_name])
                if init_val < 0.1:
                    init_val = 0.1
                elif init_val > 10:
                    init_val = 10
                sld.set(init_val)
            except:
                sld.set(1.0)

            # NOTE: We removed "self.attach_tooltip(lbl, tooltip_text)" so the label has no tooltip.
            if tooltip_text and not disabled:
                self.attach_tooltip(sld, tooltip_text)
                self.attach_tooltip(entry, tooltip_text)

            row_idx += 1

        create_timer_setting(
            param_name="hypercharge",
            label_text="Hypercharge Delay:",
            tooltip_text="How often (in seconds) the bot checks if hypercharge is ready."
        )
        create_timer_setting(
            param_name="gadget",
            label_text="Gadget Check Delay:",
            tooltip_text="How often (in seconds) the bot checks if gadget is ready."
        )
        create_timer_setting(
            param_name="wall_detection",
            label_text="Wall Detection:",
            tooltip_text="How often (in seconds) the bot detects the walls around it."
        )
        create_timer_setting(
            param_name="no_detection_proceed",
            label_text="No detections proceed Delay:",
            tooltip_text="How often (in seconds) does the bot press Q to proceed when it doesn't find the player but doesn't know in what state it is."
        )

        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

    # ---------------------------------------------------------------------------------------------
    #  Match History Tab
    # ---------------------------------------------------------------------------------------------
    def _init_history_tab(self):
        frame = self.tab_history

        scroll_frame = ctk.CTkScrollableFrame(
            frame, width=S(900), height=S(600), fg_color="transparent", corner_radius=S(10)
        )
        scroll_frame.pack(fill="both", expand=True, padx=S(10), pady=S(10))

        max_cols = 4
        row_idx = 0
        col_idx = 0

        icon_size = S(100)  # bigger icons
        for brawler, stats in self.match_history.items():
            if brawler == "total":
                continue
            icon_path = f"./api/assets/brawler_icons/{brawler}.png"
            if not os.path.exists(icon_path):
                icon_img = None
            else:
                pil_img = Image.open(icon_path).resize((icon_size, icon_size))
                icon_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(icon_size, icon_size))

            total_games = stats["victory"] + stats["defeat"]
            if total_games == 0:
                wr = lr = dr = 0
            else:
                wr = round(100 * stats["victory"] / total_games, 1)
                lr = round(100 * stats["defeat"] / total_games, 1)

            cell_frame = ctk.CTkFrame(
                scroll_frame,
                width=S(200),
                height=S(220),
                corner_radius=S(8)
            )
            cell_frame.grid(row=row_idx, column=col_idx, padx=S(15), pady=S(15))

            # Icon
            if icon_img:
                icon_label = ctk.CTkLabel(cell_frame, image=icon_img, text="")
                icon_label.pack(pady=S(5))

            # Brawler name & total games
            text_label = ctk.CTkLabel(
                cell_frame,
                text=f"{brawler}\n{total_games} games",
                font=("Arial", S(16), "bold")
            )
            text_label.pack()

            stats_frame = ctk.CTkFrame(cell_frame, fg_color="transparent")
            stats_frame.pack(pady=S(5))

            # Win in green
            color_win = "#2ecc71"

            # Loss in red
            color_loss = "#e74c3c"

            lbl_win = ctk.CTkLabel(
                stats_frame,
                text=f"{wr}%",
                font=("Arial", S(14), "bold"),
                text_color=color_win
            )
            lbl_win.pack(side="left", padx=S(5))

            lbl_loss = ctk.CTkLabel(
                stats_frame,
                text=f"{lr}%",
                font=("Arial", S(14), "bold"),
                text_color=color_loss
            )
            lbl_loss.pack(side="left", padx=S(5))

            col_idx += 1
            if col_idx >= max_cols:
                col_idx = 0
                row_idx += 1

    # ---------------------------------------------------------------------------------------------
    #  On Start => close window + callback
    # ---------------------------------------------------------------------------------------------
    def _on_start(self):
        sys.stdout.flush()
        o_out, o_err = sys.stdout, sys.stderr
        fd_out, fd_err = o_out.fileno(), o_err.fileno()
        saved_out, saved_err = os.dup(fd_out), os.dup(fd_err)
        dn = os.open(os.devnull, os.O_RDWR)
        os.dup2(dn, fd_out); os.dup2(dn, fd_err); os.close(dn)

        tkint = getattr(getattr(self, 'app', None), 'tk', None)
        renamed = False
        if tkint:
            try:
                if tkint.eval('info procs ::bgerror'):
                    tkint.eval('rename ::bgerror ::_old_bgerr'); renamed = True
                tkint.eval('proc ::bgerror args {}')
            except tk.TclError:
                pass

        try: self.app.destroy()
        except Exception: pass
        os.dup2(saved_out, fd_out); os.dup2(saved_err, fd_err)
        os.close(saved_out); os.close(saved_err)
        sys.stdout, sys.stderr = o_out, o_err

        if tkint:
            try:
                tkint.eval('rename ::bgerror {}')
                if renamed: tkint.eval('rename ::_old_bgerr ::bgerror')
            except tk.TclError: pass

        if callable(self.on_close_callback):
            self.on_close_callback()

