import json

def save_data(devices, commands, filename="resources/adb_data.json"):
    data = {
        "devices": devices,
        "commands": commands
    }
    with open(filename, "w") as f:
        json.dump(data, f)

def load_data(filename="resources/adb_data.json"):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            return data.get("devices", []), data.get("commands", [])
    except FileNotFoundError:
        return [], []