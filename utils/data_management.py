import json
import os
from cryptography.fernet import Fernet, InvalidToken


class DataManager:
    
    @staticmethod
    def load_data(filename="adb_data.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            return data.get('devices', []), data.get('commands', [])
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
    def save_data(devices=None, commands=None, filename="adb_data.json"):
        # Load existing data
        existing_devices, existing_commands = DataManager.load_data(filename)
        
        # Update data with new values if provided
        devices_to_save = devices if devices is not None else existing_devices
        commands_to_save = commands if commands is not None else existing_commands
        
        # Save data
        data = {
            "devices": devices_to_save,
            "commands": commands_to_save,
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
    
    @staticmethod
    def load_key():
        filename = "secret.key"
        if not os.path.exists(filename):
            DataManager.generate_key()
        return open(filename, "rb").read()
    
    @staticmethod
    def generate_key():
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    
    @staticmethod
    def load_credentials(filename="credentials.json"):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            key = DataManager.load_key()
            cipher_suite = Fernet(key)
            decrypted_token = DataManager.decrypt_data(data.get('telegram_token', ''), cipher_suite)
            decrypted_chat_id = DataManager.decrypt_data(data.get('telegram_chat_id', ''), cipher_suite)
            return decrypted_token, decrypted_chat_id
        except FileNotFoundError:
            print(f"File {filename} not found. Using default settings.")
            return '', ''
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {filename}. Using default settings.")
            return '', ''
        except Exception as e:
            print(f"Error during loading data: {e}. Using default settings.")
            return '', ''
    
    @staticmethod
    def save_credentials(telegram_token=None, telegram_chat_id=None, filename="credentials.json"):
        # Load existing data
        existing_token, existing_chat_id = DataManager.load_credentials(filename)
        
        # Update data with new values if provided
        telegram_token_to_save = telegram_token if telegram_token is not None else existing_token
        telegram_chat_id_to_save = telegram_chat_id if telegram_chat_id is not None else existing_chat_id
        
        # Encrypt the new token and chat_id if provided
        key = DataManager.load_key()
        cipher_suite = Fernet(key)
        encrypted_token = cipher_suite.encrypt(
            telegram_token_to_save.encode()).decode() if telegram_token_to_save else ''
        encrypted_chat_id = cipher_suite.encrypt(
            telegram_chat_id_to_save.encode()).decode() if telegram_chat_id_to_save else ''
        
        # Save data
        data = {
            "telegram_token": encrypted_token,
            "telegram_chat_id": encrypted_chat_id
        }
        print(f"Saving credentials to {filename}: {data}")
        try:
            with open(filename, "w") as f:
                json.dump(data, f)
            DataManager.log_file_contents(filename)
        except Exception as e:
            print(f"Failed to write to file {filename}: {e}")
    
    @staticmethod
    def decrypt_data(encrypted_data, cipher_suite):
        try:
            if encrypted_data:
                return cipher_suite.decrypt(encrypted_data.encode()).decode()
            else:
                return ''
        except InvalidToken:
            print("Invalid token. Returning empty string.")
            return ''
    
    @staticmethod
    def clear_telegram_credentials(filename="credentials.json"):
        data = {
            "telegram_token": '',
            "telegram_chat_id": ''
        }
        try:
            with open(filename, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to clear telegram credentials in file {filename}: {e}")
    
    @staticmethod
    def delete_command(command_to_delete, filename="adb_data.json"):
        devices, commands = DataManager.load_data(filename)
        if command_to_delete in commands:
            commands.remove(command_to_delete)
            DataManager.save_data(devices=devices, commands=commands, filename=filename)
        else:
            print(f"Command '{command_to_delete}' not found in data.")
    
    @staticmethod
    def delete_device(device_to_delete, filename="adb_data.json"):
        devices, commands = DataManager.load_data(filename)
        if device_to_delete in devices:
            devices.remove(device_to_delete)
            DataManager.save_data(devices=devices, commands=commands, filename=filename)
        else:
            print(f"Device '{device_to_delete}' not found in data.")
