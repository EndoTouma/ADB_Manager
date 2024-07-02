from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QIcon

from ui.about_tab import AboutTab
from ui.control_tab import ControlTab
from utils.data_management import DataManager

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 900
WINDOW_X_POS = 100
WINDOW_Y_POS = 100


class ADBController(QWidget):

    def __init__(self):

        super().__init__()
        
        self.devices, self.commands = DataManager.load_data()
        self.tab_control = ControlTab(self.devices, self.commands)
        
        self.init_ui()
        
        self.tab_control.refresh_device_list()
    
    def init_ui(self):

        layout = QVBoxLayout()
        tabs = QTabWidget()
        
        tab_about = AboutTab()
        tabs.addTab(self.tab_control, "Control")
        tabs.addTab(tab_about, "About")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
        
        self.setWindowTitle("ADB Controller")
        self.setGeometry(WINDOW_X_POS, WINDOW_Y_POS, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon('resources/adb.ico'))
        self.show()
    
    def save_data_method(self):

        DataManager.save_data(self.devices, self.commands)
