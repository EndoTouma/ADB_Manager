from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QApplication
from ui.about_tab import AboutTab
from ui.control_tab import ControlTab
from ui.device_monitor_tab import DeviceMonitorTab
from utils.data_management import DataManager

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 900
WINDOW_X_POS = 100
WINDOW_Y_POS = 100


class ADBManager(QWidget):
    def __init__(self, devices=None, commands=None, telegram_token='', telegram_chat_id=''):
        super().__init__()
        
        if devices is None or commands is None:
            devices, commands = DataManager.load_data()
        
        self.devices = devices
        self.commands = commands
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        
        self.tab_control = ControlTab(self.devices, self.commands)
        self.tab_about = AboutTab()
        self.tab_monitor = DeviceMonitorTab(self.devices, self.commands, self.telegram_token, self.telegram_chat_id)
        
        self.init_ui()
        self.tab_control.refresh_device_list()
    
    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        
        tab_about = AboutTab()
        tabs.addTab(self.tab_control, "Control")
        tabs.addTab(self.tab_monitor, "Monitoring")
        tabs.addTab(tab_about, "About")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
        self.setWindowTitle("ADB Manager")
        self.setGeometry(100, 100, 700, 900)
        self.setFixedSize(700, 900)
        self.setWindowIcon(QIcon('resources/adb.ico'))
        
        self.show()
