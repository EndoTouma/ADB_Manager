from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QCheckBox, QDialogButtonBox, QPushButton


class DeleteCommandDialog(QDialog):
    def __init__(self, commands, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Commands")
        self.commands = commands
        self.checkboxes = []

        layout = QVBoxLayout(self)
        self.setup_scroll_area(layout)
        self.setup_buttons(layout)
        self.setLayout(layout)

        self.setMinimumWidth(400)
        self.setMaximumWidth(self.calculate_max_checkbox_width())

    def setup_scroll_area(self, parent_layout):
        scroll_area = QScrollArea(self)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        parent_layout.addWidget(scroll_area)

        self.checkboxes = [QCheckBox(command) for command in self.commands]
        for checkbox in self.checkboxes:
            checkbox.setFixedHeight(20)
            scroll_layout.addWidget(checkbox)

    def calculate_max_checkbox_width(self):
        max_width = 350
        metrics = QFontMetrics(self.font())
        for checkbox in self.checkboxes:
            text_width = metrics.boundingRect(checkbox.text()).width()
            max_width = max(max_width, text_width)
        max_width += 50
        return max_width

    def setup_buttons(self, parent_layout):
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_commands)

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(select_all_button)
        buttons_layout.addWidget(button_box)

        parent_layout.addLayout(buttons_layout)
        parent_layout.setAlignment(button_box, Qt.AlignmentFlag.AlignRight)
    
    def select_all_commands(self):
        all_selected = all(checkbox.isChecked() for checkbox in self.checkboxes)
        for checkbox in self.checkboxes:
            checkbox.setChecked(not all_selected)
    
    def get_selected_commands(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]
