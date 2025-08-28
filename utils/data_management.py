import json
import os
import tempfile
import re as _re
from typing import Dict, List, Tuple, Optional

def _atomic_write_json(path: str, data: dict) -> None:
    dir_ = os.path.dirname(path) or "."
    os.makedirs(dir_, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, encoding="utf-8") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)


_GROUP_RE = _re.compile(r'^[\w\s\-\.\[\]\(\)]+$')


class DataManager:

    @staticmethod
    def load_data(filename: str = "adb_data.json") -> Tuple[List[str], List[str]]:

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("devices", []), data.get("commands", [])
        except FileNotFoundError:
            print(f"File {filename} not found. Using default settings.")
            return [], []
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {filename}. Using default settings.")
            return [], []
        except Exception as e:
            print(f"Error during loading data: {e}. Using default settings.")
            return [], []

    @staticmethod
    def save_data(
        devices: Optional[List[str]] = None,
        commands: Optional[List[str]] = None,
        device_groups: Optional[Dict[str, str]] = None,
        filename: str = "adb_data.json",
    ) -> None:

        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = {}
        except Exception as e:
            print(f"Error reading existing data from {filename}: {e}")
            existing = {}

        existing_devices = existing.get("devices", [])
        existing_commands = existing.get("commands", [])
        existing_groups = existing.get("device_groups", {})

        devices_to_save = devices if devices is not None else existing_devices
        commands_to_save = commands if commands is not None else existing_commands
        groups_to_save = device_groups if device_groups is not None else existing_groups

        data = {
            "devices": devices_to_save,
            "commands": commands_to_save,
            "device_groups": groups_to_save,
        }

        for k, v in existing.items():
            if k not in data:
                data[k] = v

        print(f"Saving data to {filename}: {data}")
        try:
            _atomic_write_json(filename, data)
            DataManager.log_file_contents(filename)
        except Exception as e:
            print(f"Failed to write to file {filename}: {e}")

    @staticmethod
    def log_file_contents(filename: str) -> None:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = json.load(f)
                print(f"Contents of {filename} after write: {content}")
        except Exception as e:
            print(f"Failed to read from file {filename}: {e}")

    @staticmethod
    def load_device_groups(filename: str = "adb_data.json") -> Dict[str, str]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("device_groups", {})
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            print(f"Error during loading device groups: {e}. Using empty dict.")
            return {}

    @staticmethod
    def save_device_groups(device_groups: Dict[str, str], filename: str = "adb_data.json") -> None:
        devices, commands = DataManager.load_data(filename)
        DataManager.save_data(
            devices=devices,
            commands=commands,
            device_groups=device_groups,
            filename=filename,
        )

    @staticmethod
    def validate_group_name(name: str) -> bool:
        return bool(name and len(name) <= 64 and _GROUP_RE.match(name))

    @staticmethod
    def get_all_groups(filename: str = "adb_data.json") -> List[str]:
        groups = DataManager.load_device_groups(filename).values()
        return sorted(set(groups) or {"Ungrouped"}, key=lambda s: (s != "Ungrouped", s.lower()))

    @staticmethod
    def get_devices_in_group(group: str, filename: str = "adb_data.json") -> List[str]:
        groups = DataManager.load_device_groups(filename)
        return [d for d, g in groups.items() if g == group]

    @staticmethod
    def assign_devices_to_group(devices_list: List[str], group_name: str, filename: str = "adb_data.json") -> None:
        if not DataManager.validate_group_name(group_name):
            raise ValueError("Invalid group name.")
        groups = DataManager.load_device_groups(filename)
        for d in devices_list:
            groups[d] = group_name
        DataManager.save_device_groups(groups, filename)

    @staticmethod
    def reset_devices_group(devices_list: List[str], filename: str = "adb_data.json") -> None:
        groups = DataManager.load_device_groups(filename)
        for d in devices_list:
            groups[d] = "Ungrouped"
        DataManager.save_device_groups(groups, filename)

    @staticmethod
    def rename_group(old_name: str, new_name: str, filename: str = "adb_data.json") -> None:
        if not DataManager.validate_group_name(new_name):
            raise ValueError("Invalid new group name.")
        groups = DataManager.load_device_groups(filename)
        changed = False
        for d, g in list(groups.items()):
            if g == old_name:
                groups[d] = new_name
                changed = True
        if changed:
            DataManager.save_device_groups(groups, filename)

    @staticmethod
    def delete_group(group_name: str, reassign_to: str = "Ungrouped", filename: str = "adb_data.json") -> None:
        if not DataManager.validate_group_name(reassign_to):
            raise ValueError("Invalid target group name.")
        groups = DataManager.load_device_groups(filename)
        changed = False
        for d, g in list(groups.items()):
            if g == group_name:
                groups[d] = reassign_to
                changed = True
        if changed:
            DataManager.save_device_groups(groups, filename)

    @staticmethod
    def delete_command(command_to_delete: str, filename: str = "adb_data.json") -> None:
        devices, commands = DataManager.load_data(filename)
        if command_to_delete in commands:
            commands.remove(command_to_delete)
            groups = DataManager.load_device_groups(filename)
            DataManager.save_data(
                devices=devices,
                commands=commands,
                device_groups=groups,
                filename=filename,
            )
        else:
            print(f"Command '{command_to_delete}' not found in data.")

    @staticmethod
    def delete_device(device_to_delete: str, filename: str = "adb_data.json") -> None:
        devices, commands = DataManager.load_data(filename)
        groups = DataManager.load_device_groups(filename)
        if device_to_delete in devices:
            devices.remove(device_to_delete)
            if device_to_delete in groups:
                groups.pop(device_to_delete, None)
            DataManager.save_data(
                devices=devices,
                commands=commands,
                device_groups=groups,
                filename=filename,
            )
        else:
            print(f"Device '{device_to_delete}' not found in data.")
            
    @staticmethod
    def load_ssh_connections(filename: str = "adb_data.json") -> list[dict]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            conns = data.get("ssh_connections", [])
            norm = []
            for c in conns:
                try:
                    norm.append({
                        "name": c.get("name", ""),
                        "host": c["host"],
                        "port": int(c.get("port", 22)),
                        "user": c.get("user") or "Administrator",
                        "password": c.get("password", ""),
                        "hostkey": c.get("hostkey", ""),
                    })
                
                except Exception:
                    pass
            return norm
        except Exception:
            return []

    @staticmethod
    def save_ssh_connections(connections: list[dict], filename: str = "adb_data.json") -> None:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
        existing["ssh_connections"] = connections or []
        _atomic_write_json(filename, existing)
        DataManager.log_file_contents(filename)
