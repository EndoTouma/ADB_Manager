from ui.about_tab import AboutTab
from PyQt5.QtWidgets import *
from utils.adb_executor import execute_adb_command
from utils.data_management import DataManager
from utils.command_manager import CommandManager
from utils.device_manager import DeviceManager


class ADBController(QWidget):
    def __init__(self):
        super().__init__()
        
        # Load saved data
        self.devices, self.commands = DataManager.load_data()
    

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        self.device_checkboxes = []

        tab_control = QWidget()
        tab_manage = QWidget()
        tab_about = AboutTab()

        tabs.addTab(tab_control, "Control")
        tabs.addTab(tab_manage, "Manage")
        tabs.addTab(tab_about, "About")

        # Control Tab
        layout_control = QVBoxLayout(tab_control)

        devices_label = QLabel("Available devices: ")
        devices_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.devices_grid = QGridLayout()
        self.device_checkboxes = [QCheckBox(device) for device in self.devices]

        for index, checkbox in enumerate(self.device_checkboxes):
            row = index // 4
            col = index % 4
            self.devices_grid.addWidget(checkbox, row, col)

        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(self.execute_adb_command_method)

        self.command_combobox = QComboBox()
        self.command_combobox.setEditable(False)
        self.command_combobox.addItems(self.commands)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        layout_control.addWidget(devices_label)
        layout_control.addLayout(self.devices_grid)
        command_label = QLabel("Command: ")
        command_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout_control.addWidget(command_label)
        layout_control.addWidget(self.command_combobox)
        layout_control.addWidget(execute_button)
        output_label = QLabel("Output: ")
        output_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout_control.addWidget(output_label)

        # Adding the text output widget
        layout_control.addWidget(self.output_text)

        # Manage Tab
        manage_tabs = QTabWidget(tab_manage)
        tab_manage_devices = QWidget()
        tab_manage_commands = QWidget()
        manage_tabs.addTab(tab_manage_devices, "Manage Devices")
        manage_tabs.addTab(tab_manage_commands, "Manage Commands")

        # Manage Devices Tab
        layout_manage_devices = QVBoxLayout(tab_manage_devices)

        # Add Device
        add_device_layout = QHBoxLayout()
        self.new_device_entry = QLineEdit()
        self.new_device_entry.setFixedWidth(200)
        add_device_button = QPushButton("Add Device")
        add_device_button.setFixedWidth(100)
        add_device_button.setFixedHeight(20)
        add_device_button.clicked.connect(self.add_device)
        add_device_layout.addWidget(self.new_device_entry)
        add_device_layout.addWidget(add_device_button)

        # Remove Device
        remove_device_layout = QHBoxLayout()
        self.remove_device_combo_box = QComboBox()
        self.remove_device_combo_box.setFixedWidth(200)
        self.remove_device_combo_box.addItems(self.devices)
        remove_device_button = QPushButton("Remove Device")
        remove_device_button.setFixedWidth(100)
        remove_device_button.setFixedHeight(20)
        remove_device_button.clicked.connect(self.remove_device)
        remove_device_layout.addWidget(self.remove_device_combo_box)
        remove_device_layout.addWidget(remove_device_button)

        layout_manage_devices.addLayout(add_device_layout)
        layout_manage_devices.addLayout(remove_device_layout)

        # Manage Commands Tab
        layout_manage_commands = QVBoxLayout(tab_manage_commands)

        # Add Command
        add_command_layout = QHBoxLayout()
        self.new_command_entry = QLineEdit()
        self.new_command_entry.setFixedWidth(300)

        add_command_button = QPushButton("Add Command")
        add_command_button.clicked.connect(self.add_command)
        add_command_layout.addWidget(self.new_command_entry)
        add_command_layout.addWidget(add_command_button)

        # Remove Command
        remove_command_layout = QHBoxLayout()
        self.remove_command_combobox = QComboBox()
        self.remove_command_combobox.setFixedWidth(300)
        self.remove_command_combobox.addItems(self.commands)
        remove_command_button = QPushButton("Remove Command")
        remove_command_button.clicked.connect(self.remove_command)
        remove_command_layout.addWidget(self.remove_command_combobox)
        remove_command_layout.addWidget(remove_command_button)

        layout_manage_commands.addLayout(add_command_layout)
        layout_manage_commands.addLayout(remove_command_layout)

        layout.addWidget(tabs)
        self.setLayout(layout)

        self.setWindowTitle("ADB Controller")
        self.setGeometry(100, 100, 500, 550)
        self.show()
    
    def save_data_method(self):
        DataManager.save_data(self.devices, self.commands)
    
    def execute_adb_command_method(self):
        selected_command = self.command_combobox.currentText()
        selected_devices = [checkbox.text() for checkbox in self.device_checkboxes if checkbox.isChecked()]
        for device in selected_devices:
            execute_adb_command(device, selected_command, self.output_text)
    
    def add_device(self):
        DeviceManager.add_device(
            self.devices,
            self.device_checkboxes,
            self.devices_grid,
            self.new_device_entry,
            self.remove_device_combo_box,
            self.save_data_method
        )
    
    def remove_device(self):
        DeviceManager.remove_device(
            self.devices,
            self.device_checkboxes,
            self.devices_grid,
            self.remove_device_combo_box,
            self.save_data_method
        )
    
    def add_command(self):
        CommandManager.add_command(
            self.commands,
            self.new_command_entry,
            self.command_combobox,
            self.remove_command_combobox,
            self.save_data_method
        )
    
    def remove_command(self):
        CommandManager.remove_command(
            self.commands,
            self.command_combobox,
            self.remove_command_combobox,
            self.save_data_method
        )