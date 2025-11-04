import time
import os
import pyautogui
from datetime import datetime

# CONFIG
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

INTERVAL = 2

# main
print(f"Capturing full-screen every {INTERVAL} seconds. Press Ctrl+C to stop.")
try:
    while True:
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(OUTPUT_DIR, f"screenshot_{timestamp}.png")

        # Take and save screenshot
        img = pyautogui.screenshot()
        img.save(path)
        print("Saved:", path)

        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nStopped recording.")
