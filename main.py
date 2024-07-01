import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_windows import ADBController
import resources.icons_rc  # Это необходимо для иконок

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/adb.ico'))
    
    # Установка стиля
    app.setStyle('WindowsVista')  # Можно заменить 'Fusion' на любой доступный стиль
    
    ex = ADBController()
    ex.setWindowIcon(QIcon(':/adb.ico'))
    sys.exit(app.exec())
