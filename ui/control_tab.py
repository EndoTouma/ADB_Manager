import logging
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFontMetrics, QPalette, QColor, QTextCursor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtWidgets import *

from utils.adb_executor import execute_adb_commands
from utils.data_management import DataManager
from utils.logcat_thread import LogcatThread
from utils.log_viewer import LogViewerDialog, run_log_viewer, LogHighlighter
from utils.device_status import update_device_status_ui, get_device_status
from utils.apk_manager import APKManager
from utils.command_thread import CommandThread
from utils.delete_command_dialog import DeleteCommandDialog
from utils.delete_device_dialog import DeleteDeviceDialog


class ControlTab(QWidget):
    BUTTON_WIDTH = 150
    BUTTON_HEIGHT = 23
    
    def __init__(self, devices, commands):
        super().__init__()
        self.selected_log_level = None
        self.highlighter = None
        self.output_text = None
        self.command_combobox = None
        self.devices_grid = None
        self.clear_button = None
        self.logcat_file_button = None
        self.stop_logcat_button = None
        self.logcat_button = None
        self.devices = devices
        self.commands = commands
        self.device_checkboxes = []
        self.logcat_threads = {}
        self.command_threads = {}
        self.highlight_text = ""
        self.highlight_positions = []
        self.current_highlight_index = -1
        self.init_ui()
        
        self.update_device_grid(self.devices)
        self.check_device_status()
        
        self.setAcceptDrops(True)
    
    def init_ui(self):
        layout_control = QVBoxLayout(self)
        layout_control.addWidget(self.create_group("Available Devices", self.devices_ui()))
        layout_control.addWidget(self.create_group("ADB Commands", self.commands_ui()))
        layout_control.addWidget(self.create_group("Output", self.output_ui()))
        
        self.logcat_button = QPushButton('Start Logcat')
        self.logcat_button.clicked.connect(self.select_log_level_for_logcat)
        
        self.logcat_file_button = QPushButton('Start Logcat to File')
        self.logcat_file_button.clicked.connect(self.select_log_level_for_logcat_to_file)
        
        self.stop_logcat_button = QPushButton('Stop Logcat')
        self.stop_logcat_button.clicked.connect(self.stop_logcat)
        
        logcat_button_layout = QHBoxLayout()
        logcat_button_layout.addWidget(self.logcat_button)
        logcat_button_layout.addWidget(self.logcat_file_button)
        logcat_button_layout.addWidget(self.stop_logcat_button)
        
        layout_control.addLayout(logcat_button_layout)
        
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton('Clear Output', self)
        self.clear_button.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_button)
        
        save_output_button = QPushButton('Save Output', self)
        save_output_button.clicked.connect(self.save_output_to_file)
        button_layout.addWidget(save_output_button)
        
        layout_control.addLayout(button_layout)
        self.setLayout(layout_control)
    
    def save_output_to_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
        file_dialog.setDefaultSuffix("txt")
        file_dialog.setWindowTitle("Save Output")
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path:
                return
            
            try:
                with open(file_path, 'w') as file:
                    file.write(self.output_text.toPlainText())
                QMessageBox.information(self, "Success", "Output saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save output: {str(e)}")
    
    @staticmethod
    def create_group(title, content):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addLayout(content)
        return group
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            if file_path.endswith(".apk"):
                current_text = self.command_combobox.currentText()
                new_text = f"{current_text} {file_path}".strip()
                self.command_combobox.setEditText(new_text)
    
    def commands_ui(self):
        layout = QVBoxLayout()
        self.command_combobox = QComboBox()
        self.command_combobox.setEditable(True)
        self.command_combobox.addItems(self.commands)
        self.command_combobox.setCurrentIndex(-1)
        self.command_combobox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.command_combobox)
        
        command_button_layout = QHBoxLayout()
        
        execute_button = QPushButton('Execute')
        execute_button.clicked.connect(self.execute_adb_command_method)
        command_button_layout.addWidget(execute_button)
        
        add_command_button = QPushButton('Add Command')
        add_command_button.clicked.connect(self.add_command)
        command_button_layout.addWidget(add_command_button)
        
        delete_command_button = QPushButton('Delete Command')
        delete_command_button.clicked.connect(self.delete_command)
        command_button_layout.addWidget(delete_command_button)
        
        plus_button = QPushButton("+")
        plus_button.setFixedWidth(30)
        plus_button.clicked.connect(self.handle_plus_button_click)
        command_button_layout.addWidget(plus_button)
        
        layout.addLayout(command_button_layout)
        return layout
    
    def add_device(self):
        text, ok = QInputDialog.getText(self, "Add Device", "Enter IP and Port (format: IP[:Port]):")
        if ok and text:
            try:
                parts = text.split(":")
                ip = parts[0]
                port = parts[1] if len(parts) > 1 else "5555"
                new_device = f"{ip}:{port}"
                if new_device not in self.devices:
                    self.devices.append(new_device)
                    self.update_device_grid()
                    DataManager.save_data(self.devices, self.commands)
                    self.check_device_status()
                else:
                    QMessageBox.warning(self, "Duplicate Device", "Device already exists.")
            except ValueError:
                QMessageBox.warning(self, "Invalid input", "Please use format: IP[:Port].")
    
    def delete_device(self):
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "No device selected.")
            return
        
        for device in selected_devices:
            self.devices.remove(device)
        
        self.update_device_grid()
        DataManager.save_data(self.devices, self.commands)
        self.check_device_status()
    
    def handle_plus_button_click(self):
        self.select_file_for_install()
    
    def select_file_for_install(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("APK Files (*.apk);;All Files (*)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            current_text = self.command_combobox.currentText()
            new_text = f"{current_text} {file_path}".strip()
            self.command_combobox.setEditText(new_text)
    
    def uninstall_package(self, command):
        package_name, ok = QInputDialog.getText(self, 'Uninstall Package', 'Enter package name to uninstall:')
        if ok and package_name:
            self.command_combobox.setEditText(f"uninstall {package_name}")
    
    def execute_apk_command(self, action, parameter, reinstall=False):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"<strong>{action.upper()} COMMAND</strong>: {current_time}\n")
        
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        for device in selected_devices:
            thread = CommandThread(device, f"{action} {parameter}", reinstall)
            thread.command_output.connect(self.append_output)
            thread.command_finished.connect(self.command_finished)
            self.command_threads[device] = thread
            thread.start()
    
    def append_output(self, output):
        self.output_text.append(output)
    
    def command_finished(self, device, command, success):
        if success:
            self.output_text.append(f"<strong>COMMAND {command} finished for device: {device}</strong>\n")
        else:
            self.output_text.append(f"<strong>COMMAND {command} failed for device: {device}</strong>\n")
        if device in self.command_threads:
            del self.command_threads[device]
    
    def refresh_device_list(self):
        device_status, active_devices = get_device_status()
        self.update_device_grid(active_devices)
        for checkbox in self.device_checkboxes:
            device_name = checkbox.text()
            status = device_status.get(device_name, "offline")
            update_device_status_ui(checkbox, status)
    
    def update_device_grid(self, devices=None, remove_device_combo_box=None):
        if devices is not None:
            self.devices = devices
        
        # Очистка сетки
        while self.devices_grid.count():
            item = self.devices_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Сортировка и создание чекбоксов для каждого устройства
        self.devices.sort()
        self.device_checkboxes = [QCheckBox(device) for device in self.devices]
        
        num_rows = len(self.device_checkboxes) // 4 + (len(self.device_checkboxes) % 4 != 0)
        
        for index, checkbox in enumerate(self.device_checkboxes):
            row = index // 4
            col = index % 4
            self.devices_grid.addWidget(checkbox, row, col)
        
        if remove_device_combo_box:
            remove_device_combo_box.clear()
            remove_device_combo_box.addItems(self.devices)
            remove_device_combo_box.setCurrentIndex(-1)
        
        self.devices_grid.update()
    
    def check_device_status(self):
        device_status, active_devices = get_device_status()
        for checkbox in self.device_checkboxes:
            device_name = checkbox.text()
            status = device_status.get(device_name, "offline")
            update_device_status_ui(checkbox, status)
        print(f"Device statuses updated: {[(cb.text(), cb.isChecked()) for cb in self.device_checkboxes]}")
    
    @staticmethod
    def is_device_connected(device):
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        return device in result.stdout
    
    def devices_ui(self):
        layout = QVBoxLayout()
        self.devices.sort()
        self.devices_grid = QGridLayout()
        self.update_device_grid(self.devices)
        layout.addLayout(self.devices_grid)
        
        first_row_button_layout = QHBoxLayout()
        add_device_button = QPushButton('Add Device')
        add_device_button.clicked.connect(self.add_device)
        first_row_button_layout.addWidget(add_device_button)
        
        delete_device_button = QPushButton('Delete Device')
        delete_device_button.clicked.connect(self.delete_device)
        first_row_button_layout.addWidget(delete_device_button)
        
        connect_button = QPushButton('Connect')
        connect_button.clicked.connect(self.connect_devices)
        first_row_button_layout.addWidget(connect_button)
        
        disconnect_button = QPushButton('Disconnect')
        disconnect_button.clicked.connect(self.disconnect_devices)
        first_row_button_layout.addWidget(disconnect_button)
        
        layout.addLayout(first_row_button_layout)
        
        second_row_button_layout = QHBoxLayout()
        select_all_button = QPushButton('Select All')
        select_all_button.clicked.connect(self.select_all_devices)
        second_row_button_layout.addWidget(select_all_button)
        
        refresh_button = QPushButton('Refresh Status')
        refresh_button.clicked.connect(self.refresh_device_list)
        second_row_button_layout.addWidget(refresh_button)
        
        layout.addLayout(second_row_button_layout)
        
        return layout
    
    def add_command(self):
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.setLabelText("Enter ADB Command:")
        dialog.setWindowTitle("Add Command")
        dialog.resize(400, 200)
        
        ok = dialog.exec()
        text = dialog.textValue()
        
        if ok and text:
            self.commands.append(text)
            self.command_combobox.addItem(text)
            DataManager.save_data(self.devices, self.commands)
    
    def delete_command(self):
        dialog = DeleteCommandDialog(self.commands, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            commands_to_delete = dialog.get_selected_commands()
            self.commands = [cmd for cmd in self.commands if cmd not in commands_to_delete]
            self.command_combobox.clear()
            self.command_combobox.addItems(self.commands)
            DataManager.save_data(self.devices, self.commands)
    
    def output_ui(self):
        layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        self.highlighter = LogHighlighter(self.output_text.document())
        
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.open_log_viewer)
        layout.addWidget(search_button)
        
        return layout
    
    def open_log_viewer(self):
        log_text = self.output_text.toPlainText()
        run_log_viewer(log_text)
    
    def clear_output(self):
        self.output_text.clear()
        self.highlight_positions = []
        self.current_highlight_index = -1
    
    def connect_devices(self):
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        for device in selected_devices:
            try:
                subprocess.run(['adb', 'connect', device], check=True)
                self.output_text.append(f"<strong>Connected to device: {device}</strong>\n")
            except subprocess.CalledProcessError as e:
                self.output_text.append(
                    f"<span style='color:red;'><strong>ERROR connecting to {device}: {str(e)}</strong></span>\n")
        
        self.check_device_status()
    
    def disconnect_devices(self):
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        for device in selected_devices:
            try:
                subprocess.run(['adb', 'disconnect', device], check=True)
                self.output_text.append(f"<strong>Disconnected from device: {device}</strong>\n")
            except subprocess.CalledProcessError as e:
                self.output_text.append(
                    f"<span style='color:red;'><strong>ERROR disconnecting from {device}: {str(e)}</strong></span>\n")
        
        self.check_device_status()
    
    def execute_adb_command_method(self):
        self.execute_device_command(self.command_combobox.currentText())
    
    def execute_device_command(self, command):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"<strong>{command.upper()} COMMAND</strong>: {current_time}\n")
        
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        total_execution_time = 0
        progress_dialog = QProgressDialog(f"{command.capitalize()} devices...", "Cancel", 0, len(selected_devices),
                                          self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.setMinimumWidth(400)
        
        for i, device in enumerate(selected_devices):
            if progress_dialog.wasCanceled():
                break
            progress_dialog.setValue(i)
            progress_dialog.setLabelText(f"{command.capitalize()} {device}...")
            QApplication.processEvents()
            try:
                execution_time = execute_adb_command(device, command, self.output_text)
                total_execution_time += execution_time
            except Exception as e:
                self.output_text.append(
                    f"<span style='color:red;'><strong>ERROR {command} {device}: {str(e)}</strong></span>\n")
        
        progress_dialog.setValue(len(selected_devices))
        progress_dialog.close()
        
        self.output_text.append(f"<strong>Total {command} time:</strong> {total_execution_time} seconds\n")
        self.output_text.append("<strong>-</strong>" * 120 + "\n")
        
        self.check_device_status()
    
    def select_all_devices(self):
        all_selected = all(cb.isChecked() for cb in self.device_checkboxes)
        for checkbox in self.device_checkboxes:
            checkbox.setChecked(not all_selected)
    
    def select_log_level_for_logcat(self):
        self.log_level_dialog(self.start_logcat)
    
    def select_log_level_for_logcat_to_file(self):
        self.log_level_dialog(self.start_logcat_to_file)
    
    def log_level_dialog(self, callback):
        levels = ['V (Verbose)', 'D (Debug)', 'I (Info)', 'W (Warning)', 'E (Error)', 'F (Fatal)']
        level_descriptions = {
            'V': 'Verbose: Show all log messages (the default).',
            'D': 'Debug: Show debug log messages.',
            'I': 'Info: Show informational log messages.',
            'W': 'Warning: Show warning log messages.',
            'E': 'Error: Show error log messages.',
            'F': 'Fatal: Show fatal log messages.'
        }
        level, ok = QInputDialog.getItem(self, "Select Log Level", "Log Level:", levels, 0, False)
        if ok and level:
            self.selected_log_level = level[0]
            description = level_descriptions[self.selected_log_level]
            QMessageBox.information(self, "Log Level Description", description)
            callback()
    
    def start_logcat(self):
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        for device in selected_devices:
            if device not in self.logcat_threads:
                logcat_thread = LogcatThread(device, log_level=self.selected_log_level)
                logcat_thread.logcat_output.connect(self.append_logcat_output)
                logcat_thread.finished.connect(self.logcat_finished)
                self.logcat_threads[device] = logcat_thread
                logcat_thread.start()
                self.output_text.append(f"<strong>Started logcat for device: {device}</strong>\n")
    
    def start_logcat_to_file(self):
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
        file_dialog.setDefaultSuffix("txt")
        file_dialog.setWindowTitle("Save Logcat Output")
        
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path:
                return
            
            for device in selected_devices:
                if device not in self.logcat_threads:
                    logcat_thread = LogcatThread(device, log_level="V", output_file=file_path)
                    self.logcat_threads[device] = logcat_thread
                    logcat_thread.finished.connect(self.logcat_finished)
                    logcat_thread.start()
                    self.output_text.append(f"<strong>Started logcat to file for device: {device}</strong>\n")
    
    def stop_logcat(self):
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        for device in selected_devices:
            thread = self.logcat_threads.get(device)
            if thread:
                thread.stop()
                self.output_text.append(f"<strong>Stopped logcat for device: {device}</strong>\n")
    
    def append_logcat_output(self, output):
        parts = output.split(' ', 4)
        if len(parts) < 5:
            self.output_text.append(f"<span style='color:blue;'>{output}</span>")
            return
        
        timestamp_date, timestamp_time, pid, tid, message = parts[:5]
        
        timestamp_formatted = f"<span style='font-weight:bold;color:#888888;'>{timestamp_date} {timestamp_time}</span>"
        pid_tid_formatted = f"<span style=color:#ff6e00;'>{pid} {tid}</span>"
        
        color = '#a9b7c6'
        if ' E ' in message:
            color = '#cc7832'
        elif ' W ' in message:
            color = '#ffc66d'
        elif ' I ' in message:
            color = '#6a8759'
        elif ' D ' in message:
            color = '#6897bb'
        
        self.output_text.append(
            f"{timestamp_formatted} {pid_tid_formatted} <span style='color:{color};'>{message}</span>")
    
    def logcat_finished(self, device):
        self.output_text.append(f"<strong>Logcat finished for device: {device}</strong>\n")
        if device in self.logcat_threads:
            del self.logcat_threads[device]


if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    devices = ["192.168.1.100:5555"]
    commands = ["shell getprop", "install example.apk"]
    
    main_window = QMainWindow()
    main_window.setWindowTitle("ADB Control Panel")
    
    tab_widget = QTabWidget()
    control_tab = ControlTab(devices, commands)
    tab_widget.addTab(control_tab, "Control")
    
    main_window.setCentralWidget(tab_widget)
    main_window.resize(1024, 768)
    main_window.show()
    
    sys.exit(app.exec())
