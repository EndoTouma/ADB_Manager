from PyQt5.QtWidgets import *


class ManageTab(QWidget):
    def __init__(self, devices, commands, add_device_callback, remove_device_callback, add_command_callback,
                 remove_command_callback, parent=None):
        super().__init__(parent)
        
        self.devices = devices
        self.commands = commands
        self.add_device_callback = add_device_callback
        self.remove_device_callback = remove_device_callback
        self.add_command_callback = add_command_callback
        self.remove_command_callback = remove_command_callback
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(self.create_group("Add a New Device in Available Device list", self.manage_device_ui()))
        layout.addWidget(self.create_group("Remove an Existing Device from Available Device list", self.remove_device_ui()))
        layout.addWidget(self.create_group("Add a New Command in ADB Commands list", self.add_command_ui()))
        layout.addWidget(self.create_group("Remove an Existing Command from ADB Commands list", self.remove_command_ui()))
        
        self.setLayout(layout)
    
    def create_group(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    def manage_device_ui(self):
        layout = QVBoxLayout()
        
        self.new_device_entry = QLineEdit()
        self.new_device_entry.setFixedWidth(200)
        
        add_device_button = QPushButton("Add Device")
        add_device_button.setFixedSize(200, 25)
        add_device_button.clicked.connect(self.add_device_callback)
        
        layout.addWidget(self.new_device_entry)
        layout.addWidget(add_device_button)
        
        return layout
    
    def remove_device_ui(self):
        layout = QVBoxLayout()
        
        self.remove_device_combo_box = QComboBox()
        self.remove_device_combo_box.setFixedWidth(200)
        self.remove_device_combo_box.addItems(self.devices)
        self.remove_device_combo_box.setCurrentIndex(-1)
        
        remove_device_button = QPushButton("Remove Device")
        remove_device_button.setFixedSize(200, 25)
        remove_device_button.clicked.connect(self.remove_device_callback)
        
        layout.addWidget(self.remove_device_combo_box)
        layout.addWidget(remove_device_button)
        
        return layout
    
    def add_command_ui(self):
        layout = QVBoxLayout()
        
        self.new_command_entry = QLineEdit()
        self.new_command_entry.setFixedWidth(400)
        
        add_command_button = QPushButton("Add Command")
        add_command_button.setFixedSize(200, 25)
        add_command_button.clicked.connect(self.add_command_callback)
        
        layout.addWidget(self.new_command_entry)
        layout.addWidget(add_command_button)
        
        return layout
    
    def remove_command_ui(self):
        layout = QVBoxLayout()
        
        self.remove_command_combobox = QComboBox()
        self.remove_command_combobox.setFixedWidth(400)
        self.remove_command_combobox.addItems(self.commands)
        self.remove_command_combobox.setCurrentIndex(-1)
        
        remove_command_button = QPushButton("Remove Command")
        remove_command_button.setFixedSize(200, 25)
        remove_command_button.clicked.connect(self.remove_command_callback)
        
        layout.addWidget(self.remove_command_combobox)
        layout.addWidget(remove_command_button)
        
        return layout
    
    def get_new_device_entry(self):
        return self.new_device_entry
    
    def get_remove_device_combo_box(self):
        return self.remove_device_combo_box
    
    def get_new_command_entry(self):
        return self.new_command_entry
    
    def get_remove_command_combobox(self):
        return self.remove_command_combobox