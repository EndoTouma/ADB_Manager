import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_windows import ADBController
from utils.data_management import DataManager
import resources.icons_rc

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/adb.ico'))
    
    # Загрузка данных перед созданием экземпляра
    devices, commands, theme = DataManager.load_data()
    
    # Создание экземпляра с загруженными данными
    ex = ADBController(devices, commands, theme)
    ex.setWindowIcon(QIcon(':/adb.ico'))
    
    sys.exit(app.exec())