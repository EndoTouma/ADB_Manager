import re
import socket
import subprocess
import time
import threading

import requests
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLineEdit, QPushButton, QMessageBox, QLabel

from utils.data_management import DataManager


class DeviceMonitorTab(QWidget):
    def __init__(self, devices, commands, telegram_token='', telegram_chat_id=''):
        super().__init__()
        self.devices = devices
        self.commands = commands
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.init_ui()
        self.device_status_history = {}
        self.device_event_buffer = {}
        self.buffer_lock = threading.Lock()
        self.monitor_thread = DeviceMonitorThread()
        self.monitor_thread.device_event.connect(self.buffer_device_event)
        self.monitor_thread.start()
        self.load_telegram_credentials()
        self.hostname = self.get_formatted_hostname()
        self.start_message_timer()
    
    def init_ui(self):
        layout_monitor = QVBoxLayout(self)
        
        telegram_group = self.create_telegram_ui()
        layout_monitor.addWidget(telegram_group)
        layout_monitor.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout_monitor)
    
    def start_message_timer(self):
        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.send_grouped_messages)
        self.message_timer.start(5000)
    
    def buffer_device_event(self, device, event):
        current_time = time.strftime('%d.%m.%Y %H:%M:%S')
        with self.buffer_lock:
            if self.hostname not in self.device_event_buffer:
                self.device_event_buffer[self.hostname] = []
            self.device_event_buffer[self.hostname].append(f"{current_time} - {device}: {event}")
            if device not in self.device_status_history:
                self.device_status_history[device] = {"Connected": 0, "Disconnected": 0}
            if "Connected" in event:
                self.device_status_history[device]["Connected"] += 1
            else:
                self.device_status_history[device]["Disconnected"] += 1
    
    def send_grouped_messages(self):
        with self.buffer_lock:
            for hostname, events in self.device_event_buffer.items():
                formatted_hostname = f"**{hostname} - События:**"
                formatted_events = []
                for event in events:
                    time_device, message = event.split(" - ", 1)
                    device_name, status = message.split(": ", 1)
                    emoji = "🟢" if "Connected" in status else "🚫"
                    formatted_events.append(
                        f"{emoji} {time_device} - **{device_name}**: {status}")
                message = f"{formatted_hostname}\n" + "\n".join(formatted_events)
                self.send_telegram_message(message)
            self.device_event_buffer.clear()
    
    def send_telegram_message(self, message):
        if self.telegram_token and self.telegram_chat_id:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
            requests.post(url, data=data)
    
    def connect_to_telegram(self):
        self.telegram_token = self.token_input.text()
        self.telegram_chat_id = self.chat_id_input.text()
        DataManager.save_credentials(self.telegram_token, self.telegram_chat_id)
        self.send_telegram_message("Integration with Telegram is connected.")
        QMessageBox.information(self, "Success", "Connected to Telegram successfully!")
        self.set_telegram_fields_editable(False)
        self.disconnect_button.setEnabled(True)
        
        self.token_input.hide()
        self.chat_id_input.hide()
        self.connected_label.show()
    
    def remove_integration(self):
        self.telegram_token = ''
        self.telegram_chat_id = ''
        DataManager.clear_telegram_credentials()
        self.token_input.clear()
        self.chat_id_input.clear()
        self.set_telegram_fields_editable(True)
        self.disconnect_button.setEnabled(False)
        QMessageBox.information(self, "Success", "Telegram integration removed.")
        
        self.token_input.show()
        self.chat_id_input.show()
        self.connected_label.hide()
    
    def load_telegram_credentials(self):
        token, chat_id = DataManager.load_credentials()
        if (token and chat_id):
            self.telegram_token = token
            self.telegram_chat_id = chat_id
            self.token_input.setText(self.telegram_token)
            self.chat_id_input.setText(self.telegram_chat_id)
            self.set_telegram_fields_editable(False)
            self.disconnect_button.setEnabled(True)
            
            self.token_input.hide()
            self.chat_id_input.hide()
            self.connected_label.show()
        else:
            self.set_telegram_fields_editable(True)
            self.disconnect_button.setEnabled(False)
    
    def set_telegram_fields_editable(self, editable):
        self.token_input.setReadOnly(not editable)
        self.chat_id_input.setReadOnly(not editable)
        self.connect_button.setEnabled(editable)
    
    def closeEvent(self, event):
        self.monitor_thread.stop()
        self.monitor_thread.wait()
        super().closeEvent(event)
    
    def create_telegram_ui(self):
        group = QGroupBox("Telegram Integration")
        layout = QVBoxLayout(group)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter Telegram Bot Token")
        
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("Enter Telegram Chat ID")
        
        self.connect_button = QPushButton("Connect to Telegram")
        self.connect_button.clicked.connect(self.connect_to_telegram)
        
        self.disconnect_button = QPushButton("Remove Integration")
        self.disconnect_button.clicked.connect(self.remove_integration)
        self.disconnect_button.setEnabled(False)
        
        self.connected_label = QLabel("Connected")
        self.connected_label.setStyleSheet("QLabel { color: green; }")
        self.connected_label.hide()
        
        layout.addWidget(self.token_input)
        layout.addWidget(self.chat_id_input)
        layout.addWidget(self.connected_label)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        group.setLayout(layout)
        return group
    
    def get_formatted_hostname(self):
        hostname_mapping = {
            "DESKTOP-LJB7H4O": "HUB",
            "Testers-PC54": "NODE 4",
            "testers-pc1": "NODE 1",
            "Testers-PC2": "NODE 2",
            "Testers-PC3": "NODE 3"
        }
        return hostname_mapping.get(socket.gethostname(), socket.gethostname())


class DeviceMonitorThread(QThread):
    device_event = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.previous_devices = set()
    
    def run(self):
        while self.running:
            current_devices = self.get_connected_devices()
            connected_devices = current_devices - self.previous_devices
            disconnected_devices = self.previous_devices - current_devices
            
            for device in connected_devices:
                self.device_event.emit(device, "Connected")
            
            for device in disconnected_devices:
                reason = self.get_disconnection_reason(device)
                self.device_event.emit(device, f"Disconnected (Reason: {reason})")
            
            self.previous_devices = current_devices
            time.sleep(5)
    
    def get_connected_devices(self):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, startupinfo=startupinfo)
        lines = result.stdout.strip().split('\n')[1:]
        devices = {line.split()[0] for line in lines if line.strip() and 'offline' not in line}
        return devices
    
    def get_disconnection_reason(self, device):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        providers = [
            'Microsoft-Windows-USB-USBXHCI',
            'Microsoft-Windows-USB-USBHUB3',
            'usbehci'
        ]
        
        usb_disconnect_patterns = [
            r"Device not migrated due to partial or ambiguous match.",
            r"USB device not recognized.",
            r"Device was not migrated due to a partial or ambiguous match."
        ]
        
        for provider in providers:
            command = (
                f"powershell Get-WinEvent -FilterHashtable @{{LogName='System'; "
                f"ProviderName='{provider}'}} -MaxEvents 50 | "
                "Select-Object -ExpandProperty Message"
            )
            result = subprocess.run(command, capture_output=True, text=True, shell=True, startupinfo=startupinfo)
            logs = result.stdout.split('\n')
            
            for log in logs:
                for pattern in usb_disconnect_patterns:
                    if re.search(pattern, log):
                        return log
        
        return "Device is offline or disconnected"
    
    def stop(self):
        self.running = False
