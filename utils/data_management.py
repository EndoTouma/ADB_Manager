import json

class DataManager:
    @staticmethod
    def save_data(devices, commands, filename="adb_data.json"):
        data = {
            "devices": devices,
            "commands": commands
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load_data(filename="adb_data.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                return data.get("devices", []), data.get("commands", [])
        except FileNotFoundError:
            return [], []
