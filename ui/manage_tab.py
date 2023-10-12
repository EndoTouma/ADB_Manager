from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont

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
        manage_tabs = QTabWidget(self)
        tab_manage_devices = QWidget()
        tab_manage_commands = QWidget()
        manage_tabs.addTab(tab_manage_devices, "Manage Devices")
        manage_tabs.addTab(tab_manage_commands, "Manage Commands")
        
        layout = QVBoxLayout(self)
        layout.addWidget(manage_tabs)
        self.setLayout(layout)

        
        # Manage Devices Tab
        layout_manage_devices = QVBoxLayout(tab_manage_devices)
        layout_manage_devices.addWidget(self.create_group("Add a New Device", self.manage_device_ui()))
        layout_manage_devices.addWidget(self.create_group("Remove an Existing Device", self.remove_device_ui()))
        
        # Manage Commands Tab
        layout_manage_commands = QVBoxLayout(tab_manage_commands)
        layout_manage_commands.addWidget(self.create_group("Add a New Command", self.add_command_ui()))
        layout_manage_commands.addWidget(self.create_group("Remove an Existing Command", self.remove_command_ui()))
    
    def create_group(self, title, layout):
        group = QGroupBox(title)
        group.setLayout(layout)
        return group
    
    def manage_device_ui(self):
        # Создание горизонтальных компоновок для упорядочивания виджетов в строке
        layout = QVBoxLayout()
        
        # Создание виджетов
        self.new_device_entry = QLineEdit()
        add_device_button = QPushButton("Add Device")
        add_device_button.clicked.connect(self.add_device_callback)
        
        # Определение размеров виджетов
        widget_width = 200
        button_height = 25
        self.new_device_entry.setFixedWidth(widget_width)
        add_device_button.setFixedSize(widget_width, button_height)
        
        # Добавление виджетов к компоновке
        layout.addWidget(self.new_device_entry)
        layout.addWidget(add_device_button)
        
        # Установка расстояния между виджетами и внешних отступов
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def remove_device_ui(self):
        layout = QVBoxLayout()
        
        # Создание виджетов
        self.remove_device_combo_box = QComboBox()
        remove_device_button = QPushButton("Remove Device")
        remove_device_button.clicked.connect(self.remove_device_callback)
        
        # Определение размеров виджетов
        combo_box_width = 200
        button_width = 200  # Изменено для консистентности с другими кнопками
        button_height = 25
        self.remove_device_combo_box.setFixedWidth(combo_box_width)
        remove_device_button.setFixedSize(button_width, button_height)
        
        # Добавление виджетов к компоновке
        layout.addWidget(self.remove_device_combo_box)
        layout.addWidget(remove_device_button)
        
        # Установка расстояния между виджетами и внешних отступов
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def add_command_ui(self):
        layout = QVBoxLayout()
        
        # Создание виджетов
        self.new_command_entry = QLineEdit()
        add_command_button = QPushButton("Add Command")
        add_command_button.clicked.connect(self.add_command_callback)
        
        # Определение размеров виджетов
        entry_width = 400
        button_width = 200
        button_height = 25
        self.new_command_entry.setFixedWidth(entry_width)
        add_command_button.setFixedSize(button_width, button_height)
        
        # Добавление виджетов к компоновке
        layout.addWidget(self.new_command_entry)
        layout.addWidget(add_command_button)
        
        # Установка расстояния между виджетами и внешних отступов
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def remove_command_ui(self):
        layout = QVBoxLayout()
        
        # Создание виджетов
        self.remove_command_combobox = QComboBox()
        remove_command_button = QPushButton("Remove Command")
        remove_command_button.clicked.connect(self.remove_command_callback)
        
        # Определение размеров виджетов
        combo_box_width = 400
        button_width = 200
        button_height = 25
        self.remove_command_combobox.setFixedWidth(combo_box_width)
        remove_command_button.setFixedSize(button_width, button_height)
        
        # Добавление виджетов к компоновке
        layout.addWidget(self.remove_command_combobox)
        layout.addWidget(remove_command_button)
        
        # Установка расстояния между виджетами и внешних отступов
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        return layout
    
    def get_new_device_entry(self):
        return self.new_device_entry
    
    def get_remove_device_combo_box(self):
        return self.remove_device_combo_box
    
    def get_new_command_entry(self):
        return self.new_command_entry
    
    def get_remove_command_combobox(self):
        return self.remove_command_combobox