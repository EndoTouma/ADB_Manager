from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont

from utils.adb_executor import execute_adb_command


class ControlTab(QWidget):
    def __init__(self, devices, commands):
        super().__init__()
        self.devices = devices
        self.commands = commands
        self.device_checkboxes = []
        self.init_ui()
    
    def init_ui(self):
        layout_control = QVBoxLayout(self)
        
        # Стилизация заголовков
        font_bold = QFont()
        font_bold.setBold(True)
        
        # Devices UI
        devices_group = self.create_group("Available Devices", self.devices_ui())
        
        # Commands UI
        commands_group = self.create_group("ADB Commands", self.commands_ui())
        
        # Output UI
        output_group = self.create_group("Output", self.output_ui())
        
        # Add groups to main layout
        layout_control.addWidget(devices_group)
        layout_control.addWidget(commands_group)
        layout_control.addWidget(output_group)
    
    def create_group(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    def devices_ui(self):
        layout = QVBoxLayout()
        
        self.devices.sort()
        self.devices_grid = QGridLayout()
        self.device_checkboxes = [QCheckBox(device) for device in self.devices]
        
        num_rows = len(self.device_checkboxes) // 4 + (len(self.device_checkboxes) % 4 != 0)
        
        for index, checkbox in enumerate(self.device_checkboxes):
            col = index // num_rows
            row = index % num_rows
            self.devices_grid.addWidget(checkbox, row, col)
        
        layout.addLayout(self.devices_grid)
        
        # Установка расстояния между виджетами и внешних отступов
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def commands_ui(self):
        layout = QVBoxLayout()
        
        self.command_combobox = QComboBox()
        self.command_combobox.setEditable(False)
        self.command_combobox.addItems(self.commands)
        self.command_combobox.setCurrentIndex(-1)
        
        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(self.execute_adb_command_method)
        
        layout.addWidget(self.command_combobox)
        layout.addWidget(execute_button)
        
        # Set spacing and margins
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def output_ui(self):
        layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        layout.addWidget(self.output_text)
        
        # Set spacing and margins
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def execute_adb_command_method(self):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_text.append(f"NEW COMMAND: {current_time}\n")
        
        selected_command = self.command_combobox.currentText()
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        
        if not selected_command or not selected_devices:
            QMessageBox.warning(None, "Warning", "Please select at least one device and a command to execute.")
            return
        
        total_execution_time = 0
        for device in selected_devices:
            try:
                total_execution_time += execute_adb_command(device, selected_command, self.output_text)
            except Exception as e:
                self.output_text.append(f"ERROR executing on {device}: {str(e)}\n")
        
        self.output_text.append(f"Total execution time: {total_execution_time} seconds\n")
        self.output_text.append("-" * 120 + "\n")
    
    def update_device_grid(self, devices, remove_device_combo_box=None):
        for i in reversed(range(self.devices_grid.count())):
            widget_to_remove = self.devices_grid.itemAt(i).widget()
            self.devices_grid.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
            widget_to_remove.deleteLater()
        
        devices.sort()
        self.device_checkboxes = [QCheckBox(device) for device in devices]
        
        num_rows = len(self.device_checkboxes) // 4 + (len(self.device_checkboxes) % 4 != 0)
        
        for index, checkbox in enumerate(self.device_checkboxes):
            col = index // num_rows
            row = index % num_rows
            self.devices_grid.addWidget(checkbox, row, col)
            
        if remove_device_combo_box:
            remove_device_combo_box.clear()
            remove_device_combo_box.addItems(devices)
            remove_device_combo_box.setCurrentIndex(-1)
