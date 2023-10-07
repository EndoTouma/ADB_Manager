import sys
from PyQt5.QtWidgets import QApplication
from adb_controller.ui.main_windows import ADBController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ADBController()
    sys.exit(app.exec_())