from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QApplication

from ui.about_tab import AboutTab
from ui.control_tab import ControlTab
from ui.settings_tab import SettingsTab
from utils.data_management import DataManager

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 900
WINDOW_X_POS = 100
WINDOW_Y_POS = 100


class ADBManager(QWidget):
    
    def __init__(self, devices=None, commands=None, theme=None):
        super().__init__()
        
        if devices is None or commands is None or theme is None:
            devices, commands, theme = DataManager.load_data()
        
        self.devices = devices
        self.commands = commands
        self.theme = theme
        
        self.tab_control = ControlTab(self.devices, self.commands)
        self.tab_settings = SettingsTab(self.devices, self.commands, self.theme, self)
        
        self.init_ui()
        self.tab_control.refresh_device_list()
    
    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        
        tab_about = AboutTab()
        tabs.addTab(self.tab_control, "Control")
        tabs.addTab(self.tab_settings, "Settings")
        tabs.addTab(tab_about, "About")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
        self.setWindowTitle("ADB Controller")
        self.setGeometry(WINDOW_X_POS, WINDOW_Y_POS, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon('resources/adb.ico'))
        
        self.apply_theme()
        self.show()
    
    def apply_theme(self):
        print(f"Applying theme at startup: {self.theme}")
        QApplication.instance().setStyle(self.theme)
        should_be_checked = (self.theme == "Fusion")
        if self.tab_settings.theme_toggle.isChecked() != should_be_checked:
            self.tab_settings.theme_toggle.blockSignals(True)
            self.tab_settings.theme_toggle.setChecked(should_be_checked)
            self.tab_settings.theme_toggle.blockSignals(False)
        print("Theme applied with state: ", should_be_checked)
