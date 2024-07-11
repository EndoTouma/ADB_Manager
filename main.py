import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_windows import ADBManager
from utils.data_management import DataManager
import resources.icons_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/adb.ico'))
    
    devices, commands, theme = DataManager.load_data()
    
    ex = ADBManager(devices, commands, theme)
    ex.setWindowIcon(QIcon(':/adb.ico'))
    
    sys.exit(app.exec())