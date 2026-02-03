import os
import sys

import customtkinter as ctk  # Import the customtkinter library
from gui.api import check_if_exists
from utils import api_base_url
sys.path.append(os.path.abspath('../'))
from utils import update_toml_file, load_toml_as_dict


def login(logged_in_setter):

    if api_base_url == "localhost":
        logged_in_setter(True)
        return

    def validate_api_key(api_key):
        return check_if_exists(api_key)

    def on_login_button_click():
        api_key = api_key_entry.get()
        if validate_api_key(api_key):
            result_label.configure(text="Login Successful!", text_color="green")
            logged_in_setter(True)
            app.destroy()
            update_toml_file("../cfg/login.toml", {"key": api_key})
        else:
            result_label.configure(text="Invalid API Key", text_color="red")

    login_data = load_toml_as_dict('./cfg/login.toml')
    auth_key = login_data['key']
    if auth_key and validate_api_key(auth_key):
        logged_in_setter(True)
        return

    app = ctk.CTk()
    app.title('API Key Login')
    app.geometry('500x200')
    ctk.set_appearance_mode("dark")

    label = ctk.CTkLabel(app, text="Enter API Key:", font=("Comic sans MS", 20))
    label.pack(pady=(20, 5))

    api_key_entry = ctk.CTkEntry(app, placeholder_text="API Key", font=("Comic sans MS", 20), width=400)
    api_key_entry.pack(pady=(20, 10))

    login_button = ctk.CTkButton(app, text="Login", command=on_login_button_click, font=("Comic sans MS", 25))
    login_button.pack()

    result_label = ctk.CTkLabel(app, text="")
    result_label.pack(pady=(10, 0))

    app.mainloop()
