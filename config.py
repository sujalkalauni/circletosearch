import os
import sys
import json
import winreg

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config.json"
)

DEFAULT_CONFIG = {
    "hotkey": "alt+c",
    "instant_lens": True,
    "auto_copy_ocr": False,
    "sound_effects": True,
    "floating_handle": True,
    "start_with_windows": False,
}

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "CircleToSearchWindows"


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"Error loading config: {e}")
    return config


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

    # Synchronize Windows startup registry
    update_startup_registry(config.get("start_with_windows", False))


def update_startup_registry(enable: bool):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_ALL_ACCESS
        )
        if enable:
            python_exe = sys.executable
            main_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "main.py"
            )
            # Use pythonw if available to run silently without terminal window
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            exe_to_use = (
                pythonw_exe if os.path.exists(pythonw_exe) else python_exe
            )
            cmd = f'"{exe_to_use}" "{main_script}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error updating startup registry: {e}")
