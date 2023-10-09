from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit
from PyQt5.QtCore import Qt

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout_about = QVBoxLayout(self)

        # App Name
        app_name_label = QLabel("ADB Controller")
        app_name_font = app_name_label.font()
        app_name_font.setPointSize(16)
        app_name_font.setBold(True)
        app_name_label.setFont(app_name_font)
        layout_about.addWidget(app_name_label)

        # App Version
        app_version_label = QLabel("Version: 0.0.1")
        layout_about.addWidget(app_version_label)

        # Horizontal Line
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.HLine)
        horizontal_line.setFrameShadow(QFrame.Sunken)
        layout_about.addWidget(horizontal_line)

        # Author Label
        author_label = QLabel("Author: Eugene Vervai")
        layout_about.addWidget(author_label)

        # Contact
        contact_label = QLabel("Contact: delspin1@gmail.com")
        layout_about.addWidget(contact_label)

        # License
        license_label = QLabel("License: MIT License")
        layout_about.addWidget(license_label)

        # Description
        description_label = QLabel("Description:")
        layout_about.addWidget(description_label)

        description_text = QTextEdit()
        description_text.setText(
            "ADB Controller is a user-friendly application designed to facilitate "
            "the management and control of devices via Android Debug Bridge (ADB) "
            "commands. The app allows users to easily add and remove devices and "
            "commands to suit their specific requirements, providing an intuitive "
            "graphical user interface to execute various ADB commands without the need "
            "for manual command line input.\n\n"
            "Key Features:\n"
            "    - Manage and execute ADB commands on multiple devices simultaneously.\n"
            "    - Add and remove devices and commands through a straightforward UI.\n"
            "    - Monitor command execution outputs conveniently within the application.\n\n"
            "Whether you are a developer, tester, or tech enthusiast, ADB Controller "
            "aims to enhance your workflow by providing a convenient interface for "
            "managing devices and executing ADB commands effortlessly."
        )
        description_text.setReadOnly(True)
        layout_about.addWidget(description_text)

        # Adjust spacings, alignments, etc.
        layout_about.setAlignment(Qt.AlignTop)
