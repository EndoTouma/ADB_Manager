from PyQt5.QtWidgets import QMessageBox, QCheckBox


class DeviceManager:
    
    @staticmethod
    def add_device(devices, device_checkboxes, devices_grid, new_device_entry, remove_device_combo_box,
                   save_data_method):
        try:
            new_device = new_device_entry.text()
            if new_device and new_device not in devices:
                devices.append(new_device)
                DeviceManager.update_device_grid(devices, device_checkboxes, devices_grid, remove_device_combo_box)
                new_device_entry.clear()
                remove_device_combo_box.addItem(new_device)
                save_data_method()
                QMessageBox.information(None, "Success", "Device added successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Device is empty or already exists!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
    
    @staticmethod
    def update_device_grid(devices, device_checkboxes, devices_grid,remove_device_combo_box):
        for checkbox in device_checkboxes:
            checkbox.setParent(None)
        
        devices.sort()
        device_checkboxes.clear()
        device_checkboxes.extend([QCheckBox(device) for device in devices])
        
        num_rows = len(device_checkboxes) // 4 + (len(device_checkboxes) % 4 != 0)
        
        for index, checkbox in enumerate(device_checkboxes):
            col = index // num_rows
            row = index % num_rows
            devices_grid.addWidget(checkbox, row, col)
            
        # Обновление списка устройств для удаления
        if remove_device_combo_box:
            remove_device_combo_box.clear()
            remove_device_combo_box.addItems(devices)
            remove_device_combo_box.setCurrentIndex(-1)  # Ничего не выбрано по умолчанию
    
    @staticmethod
    def remove_device(devices, device_checkboxes, devices_grid, remove_device_combo_box, save_data_method):
        try:
            remove_device = remove_device_combo_box.currentText()
            if remove_device and remove_device in devices:
                devices.remove(remove_device)
                DeviceManager.update_device_grid(devices, device_checkboxes, devices_grid, remove_device_combo_box)
                remove_device_combo_box.removeItem(remove_device_combo_box.currentIndex())
                save_data_method()
                QMessageBox.information(None, "Success", "Device removed successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Device doesn't exist or input is empty!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")