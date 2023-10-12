from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit, QGroupBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout_about = QVBoxLayout(self)

        # App Info Group
        app_info_group = self.create_group("App Information", self.app_info_ui())
        layout_about.addWidget(app_info_group)

        # Description Group
        description_group = self.create_group("Description", self.description_ui())
        layout_about.addWidget(description_group)

        layout_about.setAlignment(Qt.AlignTop)

    def create_group(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        return group

    def app_info_ui(self):
        layout = QVBoxLayout()

        # Elements: Labels and Line
        labels_text = [
            ("ADB Controller", 16, True),
            ("Version: 0.0.1", 11, False),
            ("Author: Eugene Vervai", 11, False),
            ("Contact: delspin1@gmail.com", 11, False),
            ("License: MIT License", 11, False)
        ]

        for text, size, bold in labels_text:
            label = QLabel(text)
            font = QFont()
            font.setPointSize(size)
            font.setBold(bold)
            label.setFont(font)
            layout.addWidget(label)

        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.HLine)
        horizontal_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(horizontal_line)

        layout.setSpacing(10)  # consistent spacing
        layout.setContentsMargins(10, 10, 10, 10)  # consistent margins

        return layout

    def description_ui(self):
        layout = QVBoxLayout()

        # Description Text
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

        layout.addWidget(description_text)

        layout.setSpacing(10)  # consistent spacing
        layout.setContentsMargins(10, 10, 10, 10)  # consistent margins

        return layout
