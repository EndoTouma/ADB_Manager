import logging
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFontMetrics, QPalette, QColor, QTextCursor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtWidgets import *

from utils.adb_executor import execute_adb_command
from utils.data_management import DataManager


class LogcatThread(QThread):
    logcat_output = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, device, log_level="V", output_file=None):
        super().__init__()
        self.device = device
        self.running = True
        self.output_file = output_file
        self.log_level = log_level

    def run(self):
        process = subprocess.Popen(
            ['adb', '-s', self.device, 'logcat', f'*:{self.log_level}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if self.output_file:
            with open(self.output_file, 'w') as file:
                while self.running:
                    output = process.stdout.readline().decode('utf-8')
                    if output:
                        file.write(output)
        else:
            while self.running:
                output = process.stdout.readline().decode('utf-8')
                if output:
                    self.logcat_output.emit(output)
        process.terminate()
        process.wait()
        self.finished.emit(self.device)

    def stop(self):
        self.running = False


class LogViewerDialog(QDialog):
    def __init__(self, log_text, parent=None):
        super().__init__(parent)
        self.prev_button = None
        self.next_button = None
        self.filter_button = None
        self.clear_filter_button = None
        self.search_button = None
        self.search_input = None
        self.log_viewer = None
        self.highlighter = None
        self.setWindowTitle("Log Viewer")
        self.setMinimumSize(800, 600)

        self.log_text = log_text
        self.filtered_log_text = log_text
        self.highlight_text = ""
        self.highlight_positions = []
        self.current_highlight_index = -1

        self.init_ui()
        self.update_button_states()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.log_viewer = QTextEdit(self)
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlainText(self.log_text)
        self.highlighter = LogHighlighter(self.log_viewer.document())
        layout.addWidget(self.log_viewer)

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.update_button_states)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_text)
        search_layout.addWidget(self.search_button)

        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.filter_text)
        search_layout.addWidget(self.filter_button)

        self.clear_filter_button = QPushButton("Clear Filter")
        self.clear_filter_button.clicked.connect(self.clear_filter)
        search_layout.addWidget(self.clear_filter_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.find_next)
        search_layout.addWidget(self.next_button)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.find_prev)
        search_layout.addWidget(self.prev_button)

        layout.addLayout(search_layout)

    def update_button_states(self):
        has_text = bool(self.search_input.text().strip())
        self.search_button.setEnabled(has_text)
        self.filter_button.setEnabled(has_text)
        self.clear_filter_button.setEnabled(has_text)
        self.next_button.setEnabled(False)
        self.prev_button.setEnabled(False)

    def search_text(self):
        self.highlight_text = self.search_input.text().strip()
        if not self.highlight_text:
            logging.debug('Search input is empty.')
            return

        self.log_viewer.moveCursor(QTextCursor.MoveOperation.Start)
        self.highlight_positions = []
        self.current_highlight_index = -1
        self.find_all()
        if self.highlight_positions:
            self.current_highlight_index = 0
            self.move_cursor_to_highlight()
            self.next_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            logging.debug(f'Found positions: {self.highlight_positions}')
        else:
            logging.debug('No matches found.')

    def filter_text(self):
        search_text = self.search_input.text().strip()
        if search_text:
            self.filtered_log_text = '\n'.join(
                line for line in self.log_text.split('\n') if search_text in line)
            self.log_viewer.setPlainText(self.filtered_log_text)
        else:
            self.log_viewer.setPlainText(self.log_text)

    def clear_filter(self):
        self.log_viewer.setPlainText(self.log_text)
        self.search_input.clear()
        self.update_button_states()

    def find_all(self):
        self.highlight_positions = []
        document = self.log_viewer.document()
        cursor = QTextCursor(document)

        while True:
            cursor = document.find(self.highlight_text, cursor)
            if cursor.isNull():
                break
            self.highlight_positions.append(cursor.position())

        self.highlight_search_results()

    def find_next(self):
        if not self.highlight_positions:
            logging.debug('No highlight positions available for "Next".')
            return
        self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlight_positions)
        self.move_cursor_to_highlight()

    def find_prev(self):
        if not self.highlight_positions:
            logging.debug('No highlight positions available for "Previous".')
            return
        self.current_highlight_index = (self.current_highlight_index - 1) % len(self.highlight_positions)
        self.move_cursor_to_highlight()

    def move_cursor_to_highlight(self):
        if not self.highlight_positions:
            logging.debug('No highlight positions to move to.')
            return

        cursor = self.log_viewer.textCursor()
        position = self.highlight_positions[self.current_highlight_index]
        cursor.setPosition(position - len(self.highlight_text), QTextCursor.MoveMode.MoveAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(self.highlight_text))
        self.log_viewer.setTextCursor(cursor)
        self.log_viewer.ensureCursorVisible()

    def highlight_search_results(self):
        extra_selections = []
        cursor = QTextCursor(self.log_viewer.document())
        format = QTextCharFormat()
        format.setBackground(QColor(Qt.GlobalColor.yellow))

        for pos in self.highlight_positions:
            cursor.setPosition(pos - len(self.highlight_text), QTextCursor.MoveMode.MoveAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(self.highlight_text))

            extra_selection = QTextEdit.ExtraSelection()
            extra_selection.cursor = cursor
            extra_selection.format = format
            extra_selections.append(extra_selection)

        self.log_viewer.setExtraSelections(extra_selections)


class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        timestamp_format = QTextCharFormat()
        self.highlighting_rules.append(
            (QRegularExpression("\\b\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3}\\b"), timestamp_format))

        log_level_format = QTextCharFormat()
        log_levels = ["D", "I", "W", "E", "F", "V"]
        for level in log_levels:
            self.highlighting_rules.append((QRegularExpression("\\b" + level + "\\b(?=\\s)"), log_level_format))

        message_format = QTextCharFormat()
        self.highlighting_rules.append((QRegularExpression(":.*"), message_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            match_iterator = expression.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


def update_device_status_ui(checkbox, status):
    palette = QPalette()
    if status == "device":
        palette.setColor(QPalette.ColorRole.WindowText, QColor('green'))
    elif status == "offline":
        palette.setColor(QPalette.ColorRole.WindowText, QColor('red'))
    else:
        palette.setColor(QPalette.ColorRole.WindowText, QColor('black'))
    checkbox.setPalette(palette)


def get_device_status():
    device_status = {}
    active_devices = []
    result = subprocess.run(['adb', 'devices', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    lines = result.split('\n')
    for line in lines[1:]:
        if line.strip():
            parts = line.split()
            device_name = parts[0]
            device_state = parts[1]
            device_status[device_name] = device_state
            active_devices.append(device_name)
    return device_status, active_devices


def create_group(title, layout):
    group = QGroupBox(title)
    group.setLayout(layout)
    return group


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
        text, ok = QInputDialog.getText(self, "Add Device", "Enter IP and Port (format: IP:Port):")
        if ok and text:
            try:
                ip, port = text.split(":")
                new_device = f"{ip}:{port}"
                if new_device not in self.devices:
                    self.devices.append(new_device)
                    self.update_device_grid()
                    DataManager.save_data(self.devices, self.commands)
                    self.check_device_status()
                else:
                    QMessageBox.warning(self, "Duplicate Device", "Device already exists.")
            except ValueError:
                QMessageBox.warning(self, "Invalid input", "Please use format: IP:Port.")
    
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
        progress_dialog = QProgressDialog(f"{command.capitalize()} devices...", "Cancel", 0, len(selected_devices), self)
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
                self.output_text.append(f"<span style='color:red;'><strong>ERROR {command} {device}: {str(e)}</strong></span>\n")

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

        self.output_text.append(f"{timestamp_formatted} {pid_tid_formatted} <span style='color:{color};'>{message}</span>")

    def logcat_finished(self, device):
        self.output_text.append(f"<strong>Logcat finished for device: {device}</strong>\n")
        if device in self.logcat_threads:
            del self.logcat_threads[device]


class DeleteCommandDialog(QDialog):
    def __init__(self, commands, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Commands")
        self.commands = commands
        self.checkboxes = []

        layout = QVBoxLayout(self)
        self.setup_scroll_area(layout)
        self.setup_buttons(layout)
        self.setLayout(layout)

        self.setMinimumWidth(400)
        self.setMaximumWidth(self.calculate_max_checkbox_width())

    def setup_scroll_area(self, parent_layout):
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        parent_layout.addWidget(scroll_area)

        self.checkboxes = [QCheckBox(command) for command in self.commands]
        for checkbox in self.checkboxes:
            checkbox.setFixedHeight(20)
            scroll_layout.addWidget(checkbox)

    def calculate_max_checkbox_width(self):
        max_width = 350
        metrics = QFontMetrics(self.font())
        for checkbox in self.checkboxes:
            text_width = metrics.boundingRect(checkbox.text()).width()
            max_width = max(max_width, text_width)
        max_width += 50
        return max_width

    def setup_buttons(self, parent_layout):
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_commands)

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(select_all_button)
        buttons_layout.addWidget(button_box)

        parent_layout.addLayout(buttons_layout)
        parent_layout.setAlignment(button_box, Qt.AlignmentFlag.AlignRight)

    def select_all_commands(self):
        all_selected = all(checkbox.isChecked() for checkbox in self.checkboxes)
        for checkbox in self.checkboxes:
            checkbox.setChecked(not all_selected)

    def get_selected_commands(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


class DeleteDeviceDialog(QDialog):
    def __init__(self, devices, device_statuses, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Devices")
        self.devices = devices
        self.device_statuses = device_statuses
        self.selected_devices = []

        layout = QVBoxLayout(self)

        self.checkboxes = []
        for device in devices:
            status = device_statuses.get(device)
            checkbox = QCheckBox(device)
            if status == "offline":
                checkbox.setStyleSheet("color: red;")
            else:
                checkbox.setStyleSheet("color: green;")
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_selected_devices(self):
        return [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]


class APKManager:
    @staticmethod
    def install(device, apk_path, reinstall=False):
        command = f"install {'-r' if reinstall else ''} {apk_path}".strip()
        return execute_adb_command(device, command)

    @staticmethod
    def uninstall(device, package_name):
        command = f"uninstall {package_name}"
        return execute_adb_command(device, command)


def run_log_viewer(log_text):
    viewer = LogViewerDialog(log_text)
    viewer.exec()


class CommandThread(QThread):
    command_finished = pyqtSignal(str, str, bool)
    command_output = pyqtSignal(str)

    def __init__(self, device, command, reinstall=False, parent=None):
        super().__init__(parent)
        self.device = device
        self.command = command
        self.reinstall = reinstall

    def run(self):
        try:
            if "install" in self.command:
                apk_path = self.command.split(" ")[1]
                output = APKManager.install(self.device, apk_path, self.reinstall)
            elif "uninstall" in self.command:
                package_name = self.command.split(" ")[1]
                output = APKManager.uninstall(self.device, package_name)
            self.command_output.emit(output)
            self.command_finished.emit(self.device, self.command, True)
        except Exception as e:
            self.command_output.emit(str(e))
            self.command_finished.emit(self.device, self.command, False)