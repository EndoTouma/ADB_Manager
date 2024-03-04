import subprocess
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFontMetrics, QPalette, QColor
from PyQt5.QtCore import Qt

from utils.adb_executor import execute_adb_command
from utils.data_management import DataManager


class ControlTab(QWidget):
    BUTTON_WIDTH = 150
    BUTTON_HEIGHT = 23
    SMALL_BUTTON_WIDTH = 150
    SMALL_BUTTON_HEIGHT = 23
    
    def __init__(self, devices, commands):
        super().__init__()
        self.devices = devices
        self.commands = commands
        self.device_checkboxes = []
        self.devices, self.commands = DataManager.load_data()
        self.init_ui()
    
    def init_ui(self):
        layout_control = QVBoxLayout(self)
        devices_group = self.create_group("Available Devices", self.devices_ui())
        commands_group = self.create_group("ADB Commands", self.commands_ui())
        output_group = self.create_group("Output", self.output_ui())
        layout_control.addWidget(devices_group)
        layout_control.addWidget(commands_group)
        layout_control.addWidget(output_group)
        self.refresh_button = QPushButton('Refresh Status', self)
        self.refresh_button.clicked.connect(self.refresh_device_list)
        layout_control.addWidget(self.refresh_button)
        self.check_device_status()
    
    def refresh_device_list(self):
        device_status, active_devices = self.get_device_status()
        self.update_device_grid(active_devices)
        for checkbox in self.device_checkboxes:
            device_name = checkbox.text()
            if device_name in device_status:
                self.update_device_status_ui(checkbox, device_status[device_name])
            else:
                self.update_device_status_ui(checkbox, "disconnected")
    
    def get_device_status(self):
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
    
    def update_device_grid(self, active_devices):
        existing_devices = [cb.text() for cb in self.device_checkboxes]
        for device in active_devices:
            if device not in existing_devices:
                checkbox = QCheckBox(device)
                self.device_checkboxes.append(checkbox)
                row, col = divmod(len(self.device_checkboxes) - 1, 4)
                self.devices_grid.addWidget(checkbox, row, col)
    
    def update_device_status_ui(self, checkbox, status):
        palette = QPalette()
        if status == "device":
            palette.setColor(QPalette.Active, QPalette.WindowText, QColor('green'))
        elif status == "offline":
            palette.setColor(QPalette.Active, QPalette.WindowText, QColor('red'))
        else:
            palette.setColor(QPalette.Active, QPalette.WindowText, QColor('black'))
        checkbox.setPalette(palette)
    
    def check_device_status(self):
        for checkbox in self.device_checkboxes:
            device = checkbox.text()
            if self.is_device_connected(device):
                self.update_device_status_ui(checkbox, "connected")
            else:
                self.update_device_status_ui(checkbox, "disconnected")
    
    @staticmethod
    def is_device_connected(device):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, startupinfo=startupinfo)
        return device in result.stdout
    
    def create_group(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    def devices_ui(self):
        layout = QVBoxLayout()
        self.devices.sort()
        self.devices_grid = QGridLayout()
        self.device_checkboxes = [QCheckBox(device) for device in self.devices]
        for index, checkbox in enumerate(self.device_checkboxes):
            row, col = divmod(index, 4)
            self.devices_grid.addWidget(checkbox, row, col)
        layout.addLayout(self.devices_grid)
        
        # Adding Select All, Connect, and Disconnect buttons
        button_layout = QHBoxLayout()
        
        select_all_button = QPushButton('Select All')
        select_all_button.clicked.connect(self.select_all_devices)
        button_layout.addWidget(select_all_button)
        
        connect_button = QPushButton('Connect')
        connect_button.clicked.connect(self.connect_devices)
        button_layout.addWidget(connect_button)
        
        disconnect_button = QPushButton('Disconnect')
        disconnect_button.clicked.connect(self.disconnect_devices)
        button_layout.addWidget(disconnect_button)
        
        layout.addLayout(button_layout)
        
        self.apply_standard_margins_and_spacing(layout)
        return layout
    
    def commands_ui(self):
        layout = QVBoxLayout()
        self.command_combobox = QComboBox()
        self.command_combobox.setEditable(False)
        self.command_combobox.addItems(self.commands)
        self.command_combobox.setCurrentIndex(-1)
        self.command_combobox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.command_combobox)
        
        # Creating buttons in a horizontal layout
        button_layout = QHBoxLayout()
        
        execute_button = QPushButton('Execute')
        execute_button.clicked.connect(self.execute_adb_command_method)
        button_layout.addWidget(execute_button)
        
        add_command_button = QPushButton('Add Command')
        add_command_button.clicked.connect(self.add_command)
        button_layout.addWidget(add_command_button)
        
        delete_command_button = QPushButton('Delete Command')
        delete_command_button.clicked.connect(self.delete_command)
        button_layout.addWidget(delete_command_button)
        
        layout.addLayout(button_layout)
        
        self.apply_standard_margins_and_spacing(layout)
        return layout
    
    def add_command(self):
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setLabelText("Enter ADB Command:")
        dialog.setWindowTitle("Add Command")
        dialog.resize(400, 200)
        
        ok = dialog.exec_()
        text = dialog.textValue()
        
        if ok and text:
            self.commands.append(text)
            self.command_combobox.addItem(text)
            DataManager.save_data(self.devices, self.commands)
    
    def delete_command(self):
        dialog = DeleteCommandDialog(self.commands, parent=self)
        if dialog.exec_() == QDialog.Accepted:
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
        self.apply_standard_margins_and_spacing(layout)
        return layout
    
    def create_button_layout(self, buttons, add_stretch=False):
        button_layout = QHBoxLayout()
        if add_stretch:
            button_layout.addStretch(1)
        for text, callback in buttons:
            button = self.create_button(text, callback)
            button_layout.addWidget(button)
        if not add_stretch:
            button_layout.addStretch(1)
        return button_layout
    
    def create_button(self, text, callback):
        button = QPushButton(text)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button.clicked.connect(callback)
        return button
    
    def apply_standard_margins_and_spacing(self, layout):
        layout.setSpacing(10)
    
    def connect_devices(self):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"<strong>CONNECT COMMAND</strong>: {current_time}\n")
        
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device to connect.")
            return
        
        total_execution_time = 0
        progress_dialog = QProgressDialog("Connecting devices...", None, 0, len(selected_devices), self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.setMinimumWidth(400)
        
        for i, device in enumerate(selected_devices):
            if progress_dialog.wasCanceled():
                break
            progress_dialog.setValue(i)
            progress_dialog.setLabelText(f"Connecting {device}...")
            QApplication.processEvents()  # Update the dialog's appearance
            try:
                total_execution_time += execute_adb_command(device, "connect", self.output_text)
            except Exception as e:
                self.output_text.append(f"ERROR connecting {device}: {str(e)}\n")
        
        progress_dialog.setValue(len(selected_devices))
        progress_dialog.close()
        self.output_text.append(f"<strong>Total connection time</strong>: {total_execution_time} seconds\n")
        self.output_text.append("<strong>-</strong>" * 120 + "\n")
        
        self.check_device_status()
    
    
    def disconnect_devices(self):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"<strong>DISCONNECT COMMAND</strong>: {current_time}\n")
        
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device to disconnect.")
            return
        
        total_execution_time = 0
        progress_dialog = QProgressDialog("Disconnecting devices...", None, 0, len(selected_devices), self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.setMinimumWidth(400)
        
        for i, device in enumerate(selected_devices):
            if progress_dialog.wasCanceled():
                break
            progress_dialog.setValue(i)
            progress_dialog.setLabelText(f"Disconnecting {device}...")
            QApplication.processEvents()  # Update the dialog's appearance
            try:
                total_execution_time += execute_adb_command(device, "disconnect", self.output_text)
            except Exception as e:
                self.output_text.append(f"ERROR disconnecting {device}: {str(e)}\n")
        
        progress_dialog.setValue(len(selected_devices))
        progress_dialog.close()
        self.output_text.append(f"<strong>Total disconnection time</strong>: {total_execution_time} seconds\n")
        self.output_text.append("<strong>-</strong>" * 120 + "\n")
        
        self.check_device_status()  # Обновление статуса устройства после попытки отключения
    
    def execute_adb_command_method(self):
        """
        Execute the selected ADB command on the selected devices.
        Append the output and any errors to the output_text QTextEdit.
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"<strong>NEW COMMAND</strong>: {current_time}\n")
        
        selected_command = self.command_combobox.currentText()
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        
        if not selected_command or not selected_devices:
            QMessageBox.warning(None, "Warning", "Please select at least one device and a command to execute.")
            return
        
        total_execution_time = 0
        progress_dialog = QProgressDialog("Executing commands...", "Cancel", 0, len(selected_devices), self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.setMinimumWidth(400)
        
        for i, device in enumerate(selected_devices):
            if progress_dialog.wasCanceled():
                break
            progress_dialog.setValue(i)
            progress_dialog.setLabelText(f"Executing on {device}...")
            QApplication.processEvents()  # Update the dialog's appearance
            try:
                execution_time = execute_adb_command(device, selected_command, self.output_text)
                total_execution_time += execution_time
            except Exception as e:
                self.output_text.append(f"ERROR executing on {device}: {str(e)}\n")
        
        progress_dialog.setValue(len(selected_devices))
        
        progress_dialog.close()
        
        self.output_text.append(f"<strong>Total execution time:</strong> {total_execution_time} seconds\n")
        self.output_text.append("<strong>-</strong>" * 120 + "\n")
    
    def update_device_grid(self, devices, remove_device_combo_box=None):
        """
        Update the grid layout which shows devices checkboxes.

        :param devices: List of devices to be shown on the grid.
        :param remove_device_combo_box: (Optional) QComboBox that might need updating with the new device list.
        """
        # Clearing existing widgets in the layout.
        for i in reversed(range(self.devices_grid.count())):
            widget_to_remove = self.devices_grid.itemAt(i).widget()
            self.devices_grid.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
            widget_to_remove.deleteLater()
        
        devices.sort()
        self.device_checkboxes = [QCheckBox(device) for device in devices]
        
        num_rows = len(self.device_checkboxes) // 4 + (len(self.device_checkboxes) % 4 != 0)
        
        # Adding checkboxes to the layout.
        for index, checkbox in enumerate(self.device_checkboxes):
            col = index // num_rows
            row = index % num_rows
            self.devices_grid.addWidget(checkbox, row, col)
        
        # Updating the remove_device_combo_box if provided.
        if remove_device_combo_box:
            remove_device_combo_box.clear()
            remove_device_combo_box.addItems(devices)
            remove_device_combo_box.setCurrentIndex(-1)
    
    def select_all_devices(self):
        """
        Toggles the selection of all device checkboxes. If all are selected,
        all checkboxes will be deselected, and vice versa.
        """
        all_selected = all(cb.isChecked() for cb in self.device_checkboxes)
        for checkbox in self.device_checkboxes:
            checkbox.setChecked(not all_selected)
            

class DeleteCommandDialog(QDialog):
    def __init__(self, commands, parent=None):
        """
        Initialize the DeleteCommandDialog.

        :param commands: a list of command names.
        :param parent: parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Delete Commands")
        
        self.commands = commands
        self.checkboxes = []
        
        layout = QVBoxLayout(self)
        
        self.setup_scroll_area(layout)
        self.setup_buttons(layout)
        
        self.setLayout(layout)
        
        self.setMinimumWidth(400)  # Set the minimum width of the window to 400 pixels
        self.setMaximumWidth(self.calculate_max_checkbox_width())  # Set the max width based on the content
    
    def setup_scroll_area(self, parent_layout):
        """
        Set up the scroll area for command checkboxes.

        :param parent_layout: layout to which the scroll area is added.
        """
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        parent_layout.addWidget(scroll_area)
        
        self.checkboxes = [QCheckBox(command) for command in self.commands]
        
        max_width = self.calculate_max_checkbox_width()
        
        max_window_width = 500
        if max_width > max_window_width:
            max_width = max_window_width
        
        self.setMaximumWidth(max_width)
        
        for checkbox in self.checkboxes:
            checkbox.setFixedHeight(20)
            scroll_layout.addWidget(checkbox)
    
    def calculate_max_checkbox_width(self):
        """
        Calculate the maximum width needed for the checkboxes based on their label texts.

        :return: max width.
        """
        max_width = 350
        metrics = QFontMetrics(self.font())
        for checkbox in self.checkboxes:
            text_width = metrics.boundingRect(checkbox.text()).width()
            max_width = max(max_width, text_width)
        max_width += 50  # Adding some padding
        return max_width
    
    def setup_buttons(self, parent_layout):
        """
        Set up the dialog buttons.

        :param parent_layout: layout to which buttons are added.
        """
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_commands)
        
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(select_all_button)
        buttons_layout.addWidget(button_box)
        
        parent_layout.addLayout(buttons_layout)
        parent_layout.setAlignment(button_box, Qt.AlignRight)
    
    def select_all_commands(self):
        """
        Check or uncheck all command checkboxes based on the current state.
        """
        all_selected = all(checkbox.isChecked() for checkbox in self.checkboxes)
        
        for checkbox in self.checkboxes:
            checkbox.setChecked(not all_selected)
    
    def get_selected_commands(self):
        """
        Get all selected commands.

        :return: a list of selected command names.
        """
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]