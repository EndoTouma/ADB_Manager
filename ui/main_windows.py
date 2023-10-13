from PyQt5.QtWidgets import *

from ui.about_tab import AboutTab
from ui.control_tab import ControlTab
from ui.manage_tab import ManageTab
from utils.command_manager import CommandManager
from utils.data_management import DataManager
from utils.device_manager import DeviceManager


class ADBController(QWidget):
    def __init__(self):
        super().__init__()
        
        self.devices, self.commands = DataManager.load_data()
        self.tab_control = ControlTab(self.devices, self.commands)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        self.device_checkboxes = []
        
        tab_about = AboutTab()
        
        tabs.addTab(self.tab_control, "Control")
        
        self.tab_manage = ManageTab(
            self.devices,
            self.commands,
            self.add_device,
            self.remove_device,
            self.add_command,
            self.remove_command,
            parent=self
        )
        tabs.addTab(self.tab_manage, "Manage")
        
        tabs.addTab(tab_about, "About")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
        self.setWindowTitle("ADB Controller")
        self.setGeometry(100, 100, 500, 550)
        self.show()
    
    def save_data_method(self):
        DataManager.save_data(self.devices, self.commands)
    
    def add_device(self):
        DeviceManager.add_device(
            self.devices,
            self.tab_control,
            self.tab_manage.get_new_device_entry(),
            self.tab_manage.get_remove_device_combo_box(),
            self.save_data_method
        )
    
    def remove_device(self):
        DeviceManager.remove_device(
            self.devices,
            self.tab_control,
            self.tab_manage.get_remove_device_combo_box(),
            self.save_data_method
        )
    
    def add_command(self):
        try:
            CommandManager.add_command(
                self.commands,
                self.tab_manage.get_new_command_entry(),
                self.tab_control.command_combobox,
                self.tab_manage.get_remove_command_combobox(),
                self.save_data_method
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def remove_command(self):
        try:
            CommandManager.remove_command(
                self.commands,
                self.tab_control.command_combobox,
                self.tab_manage.get_remove_command_combobox(),
                self.save_data_method
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
