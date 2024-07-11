import json
import os


class DataManager:
    
    @staticmethod
    def load_data(filename="adb_data.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            return data.get('devices', []), data.get('commands', []), data.get('theme', 'WindowsVista')
        except FileNotFoundError:
            print(f"File {filename} not found. Using default settings.")
            return [], [], 'WindowsVista'
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {filename}. Using default settings.")
            return [], [], 'WindowsVista'

    @staticmethod
    def save_data(devices, commands, theme="WindowsVista", filename="adb_data.json"):
        data = {
            "devices": devices,
            "commands": commands,
            "theme": theme
        }
        print(f"Saving data to {filename}: {data}")
        try:
            with open(filename, "w") as f:
                json.dump(data, f)
            DataManager.log_file_contents(filename)
        except Exception as e:
            print(f"Failed to write to file {filename}: {e}")

    @staticmethod
    def log_file_contents(filename):
        try:
            with open(filename, "r") as f:
                content = json.load(f)
                print(f"Contents of {filename} after write: {content}")
        except Exception as e:
            print(f"Failed to read from file {filename}: {e}")
