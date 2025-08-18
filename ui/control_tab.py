import subprocess
import re
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QFileDialog, QMessageBox, QProgressDialog, QApplication,
    QTextEdit, QPushButton, QComboBox, QSizePolicy, QInputDialog, QCheckBox
)

from utils.command_thread import CommandThread
from utils.data_management import DataManager
from utils.delete_command_dialog import DeleteCommandDialog
from utils.adb_executor import ADBWorker
from utils.device_status import update_device_status_ui, get_device_status
from utils.log_viewer import run_log_viewer, LogHighlighter
from utils.logcat_thread import LogcatThread


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

        self.device_groups = DataManager.load_device_groups()
        self.group_names_cache = set(self.device_groups.values())

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

    @staticmethod
    def create_group(title, content_layout):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addLayout(content_layout)
        return group

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            if file_path.endswith(".apk"):
                if " " in file_path or any(ord(ch) > 127 for ch in file_path):
                    file_path = f'"{file_path}"'
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
        
        run_group_button = QPushButton('Run on Group')
        run_group_button.clicked.connect(self.run_command_on_group)
        command_button_layout.addWidget(run_group_button)

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

    def handle_plus_button_click(self):
        self.select_file_for_install()

    def select_file_for_install(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("APK Files (*.apk);;All Files (*)")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if " " in file_path or any(ord(ch) > 127 for ch in file_path):
                file_path = f'"{file_path}"'
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
        self.check_device_status()
    
    def check_device_status(self):
        device_status, connected_devices = get_device_status()
        
        all_devices = sorted(set(self.devices) | set(connected_devices))
        
        self.update_device_grid(all_devices)
        
        for checkbox in self.device_checkboxes:
            device_name = checkbox.text()
            status = device_status.get(device_name, "offline")
            update_device_status_ui(checkbox, status)
    
    def update_device_grid(self, devices=None, remove_device_combo_box=None):
        if devices is None:
            devices = self.devices
        
        self.devices = sorted(devices)
        
        if self.devices_grid is None:
            self.devices_grid = QVBoxLayout()
        
        while self.devices_grid.count():
            item = self.devices_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        
        groups_map = {}
        for dev in self.devices:
            group = self.device_groups.get(dev, "Ungrouped")
            groups_map.setdefault(group, []).append(dev)
        
        self.group_names_cache = set(self.device_groups.values())
        
        self.device_checkboxes = []
        
        for group_name in sorted(groups_map.keys(), key=lambda s: (s != "Ungrouped", s.lower())):
            group_box = QGroupBox(f"{group_name} ({len(groups_map[group_name])})")
            grid = QGridLayout()
            
            devs = groups_map[group_name]
            for index, dev in enumerate(devs):
                cb = QCheckBox(dev)
                self.device_checkboxes.append(cb)
                row, col = divmod(index, 4)
                grid.addWidget(cb, row, col)
            
            controls = QHBoxLayout()
            select_btn = QPushButton("Select group")
            unselect_btn = QPushButton("Unselect group")
            
            def make_select(devices_in_group):
                return lambda: [cb.setChecked(True) for cb in self.device_checkboxes if cb.text() in devices_in_group]
            
            def make_unselect(devices_in_group):
                return lambda: [cb.setChecked(False) for cb in self.device_checkboxes if cb.text() in devices_in_group]
            
            select_btn.clicked.connect(make_select(devs))
            unselect_btn.clicked.connect(make_unselect(devs))
            controls.addWidget(select_btn)
            controls.addWidget(unselect_btn)
            
            outer_v = QVBoxLayout()
            outer_v.addLayout(grid)
            outer_v.addLayout(controls)
            group_box.setLayout(outer_v)
            
            self.devices_grid.addWidget(group_box)
        
        if remove_device_combo_box:
            remove_device_combo_box.clear()
            remove_device_combo_box.addItems(self.devices)
            remove_device_combo_box.setCurrentIndex(-1)
    
    @staticmethod
    def is_device_connected(device):
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        return device in result.stdout

    def devices_ui(self):
        layout = QVBoxLayout()

        self.devices.sort()
        self.devices_grid = QVBoxLayout()
        self.update_device_grid(self.devices)
        layout.addLayout(self.devices_grid)

        first_row_button_layout = QHBoxLayout()
        layout.addLayout(first_row_button_layout)

        second_row_button_layout = QHBoxLayout()

        assign_group_btn = QPushButton('Assign Group')
        assign_group_btn.clicked.connect(self.assign_group_for_selected)
        second_row_button_layout.addWidget(assign_group_btn)

        reset_group_btn = QPushButton('Reset Group')
        reset_group_btn.clicked.connect(self.reset_group_for_selected)
        second_row_button_layout.addWidget(reset_group_btn)

        select_all_button = QPushButton('Select All')
        select_all_button.clicked.connect(self.select_all_devices)
        second_row_button_layout.addWidget(select_all_button)

        refresh_button = QPushButton('Refresh Status')
        refresh_button.clicked.connect(self.refresh_device_list)
        second_row_button_layout.addWidget(refresh_button)

        layout.addLayout(second_row_button_layout)

        return layout

    def _get_selected_devices(self):
        return [cb.text() for cb in self.device_checkboxes if cb.isChecked()]
    
    def _restore_selected_devices(self, selected_names: list[str]):
        name_set = set(selected_names)
        for cb in self.device_checkboxes:
            cb.setChecked(cb.text() in name_set)
    
    def _select_devices_by_names(self, names: list[str]):
        name_set = set(names)
        for cb in self.device_checkboxes:
            cb.setChecked(cb.text() in name_set)
    
    def run_command_on_group(self):
        command = (self.command_combobox.currentText() or "").strip()
        if not command:
            QMessageBox.warning(self, "Warning", "Please enter/select an ADB command first.")
            return
        
        groups_map = {}
        for d in self.devices:
            g = self.device_groups.get(d, "Ungrouped")
            groups_map.setdefault(g, []).append(d)
        
        if not groups_map:
            QMessageBox.information(self, "No Devices", "No devices available.")
            return
        
        group_names_sorted = sorted(groups_map.keys(), key=lambda s: (s != "Ungrouped", s.lower()))
        display_items = [f"{name} ({len(groups_map[name])})" for name in group_names_sorted]
        
        item, ok = QInputDialog.getItem(
            self, "Run on Group", "Select group to run the command:", display_items, 0, False
        )
        if not ok or not item:
            return
        
        chosen_group = item.rsplit(" (", 1)[0]
        devices_in_group = groups_map.get(chosen_group, [])
        
        if not devices_in_group:
            QMessageBox.information(self, "Empty Group", f"No devices in '{chosen_group}'.")
            return
        
        prev_selected = self._get_selected_devices()
        self._select_devices_by_names(devices_in_group)
        
        self.execute_device_command(command)
        
        self._select_devices_by_names(prev_selected)
    
    def assign_group_for_selected(self):
        selected = self._get_selected_devices()
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        suggestions = sorted(self.group_names_cache | {"Ungrouped"})
        
        group, ok = QInputDialog.getItem(
            self,
            "Assign Group",
            "Group name:",
            suggestions,
            0,
            True
        )
        if not ok:
            return
        
        group = (group or "").strip()
        if not group:
            QMessageBox.warning(self, "Warning", "Group name cannot be empty.")
            return
        
        for dev in selected:
            self.device_groups[dev] = group
        self.group_names_cache.add(group)
        
        DataManager.save_device_groups(self.device_groups)
        
        selected_now = self._get_selected_devices()
        
        self.check_device_status()
        
        self._restore_selected_devices(selected_now)
    
    def reset_group_for_selected(self):
        selected = self._get_selected_devices()
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return

        for dev in selected:
            self.device_groups[dev] = "Ungrouped"
        
        DataManager.save_device_groups(self.device_groups)
        
        selected_now = self._get_selected_devices()
        self.check_device_status()
        self._restore_selected_devices(selected_now)

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
            DataManager.save_data(self.devices, self.commands, DataManager.load_device_groups())

    def delete_command(self):
        dialog = DeleteCommandDialog(self.commands, parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            commands_to_delete = dialog.get_selected_commands()
            self.commands = [cmd for cmd in self.commands if cmd not in commands_to_delete]
            self.command_combobox.clear()
            self.command_combobox.addItems(self.commands)
            DataManager.save_data(self.devices, self.commands, DataManager.load_device_groups())

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
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.output_text.toPlainText())
                QMessageBox.information(self, "Success", "Output saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save output: {e}")

    def execute_adb_command_method(self):
        self.execute_device_command(self.command_combobox.currentText())
    
    def execute_device_command(self, command):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"<strong>{command.upper()} COMMAND</strong>: {current_time}\n")
        
        self.selected_devices_exec = [cb.text() for cb in self.device_checkboxes if cb.isChecked()]
        if not self.selected_devices_exec:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        
        self.is_install_cmd_exec = command.strip().lower().startswith("install ")
        self.total_devices_exec = len(self.selected_devices_exec)
        self.completed_devices_exec = 0
        self.device_start_times = {}
        
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setWindowTitle(
            f"ADB Manager - {'Installing' if self.is_install_cmd_exec else 'Executing'}")
        self.progress_dialog.setLabelText(
            f"{'Installing' if self.is_install_cmd_exec else 'Executing'} on 1 of {self.total_devices_exec}..."
        )
        self.progress_dialog.setCancelButtonText("Cancel")
        self.progress_dialog.setRange(0, 0)  # бесконечная анимация
        self.progress_dialog.setMinimumWidth(400)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        for device in self.selected_devices_exec:
            self.device_start_times[device] = datetime.now()
            thread = CommandThread(device, command)
            thread.command_output.connect(self.append_output)

            thread.command_finished.connect(self._device_finished)
            self.command_threads[device] = thread
            thread.start()
    
    def _device_finished(self, device, command, success, elapsed):
        self.completed_devices_exec += 1
        
        if self.progress_dialog.minimum() == 0 and self.progress_dialog.maximum() == 0:
            self.progress_dialog.setRange(0, self.total_devices_exec)
        
        self.progress_dialog.setValue(self.completed_devices_exec)
        self.progress_dialog.setLabelText(
            f"{'Installing' if self.is_install_cmd_exec else 'Executing'} on {device} "
            f"({self.completed_devices_exec} of {self.total_devices_exec})"
        )
        
        color = "green" if success else "red"
        status = "SUCCESS" if success else "FAILED"
        self.output_text.append(
            f"<span style='color:{color};'><strong>{command} {status}</strong> on {device} "
            f"({elapsed:.2f} sec)</span>\n"
        )
        
        if self.completed_devices_exec >= self.total_devices_exec:
            self.progress_dialog.close()
            QMessageBox.information(self, "Execution Complete",
                                    f"{command} completed for all devices")
    
    def _update_progress(self, device, percent):
        self.progress_dialog.setLabelText(
            f"{'Installing' if self.is_install_cmd_exec else 'Executing'} on {device} "
            f"({self.completed_devices_exec} of {self.total_devices_exec}) — {percent}%"
        )
        QApplication.processEvents()

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
                    log_level = self.selected_log_level or "V"
                    logcat_thread = LogcatThread(device, log_level=log_level, output_file=file_path)
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
        pid_tid_formatted = f"<span style='color:#ff6e00;'>{pid} {tid}</span>"

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