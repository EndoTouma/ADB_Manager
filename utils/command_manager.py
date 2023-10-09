from PyQt5.QtWidgets import QMessageBox, QCheckBox


class CommandManager:
    
    @staticmethod
    def add_command(commands, new_command_entry, command_combobox, remove_command_combobox, save_data_method):
        try:
            new_command = new_command_entry.text()
            if new_command and new_command not in commands:
                commands.append(new_command)
                new_command_entry.clear()
                save_data_method()
                command_combobox.addItem(new_command)
                remove_command_combobox.addItem(new_command)
                QMessageBox.information(None, "Success", "Command added successfully!")
            else:
                QMessageBox.warning(None, "Warning", "Command is empty or already exists!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
    
    @staticmethod
    def remove_command(commands, command_combobox, remove_command_combobox, save_data_method):
        try:
            remove_command = remove_command_combobox.currentText()
            if remove_command and remove_command in commands:
                commands.remove(remove_command)
                index_to_remove = command_combobox.findText(remove_command)
                command_combobox.removeItem(index_to_remove)
                index_to_remove_remove_section = remove_command_combobox.findText(remove_command)
                remove_command_combobox.removeItem(index_to_remove_remove_section)
                save_data_method()
                QMessageBox.information(None, "Success", "Command successfully removed!")
            else:
                QMessageBox.warning(None, "Error", "Command doesn't exist!")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
