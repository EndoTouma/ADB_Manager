import subprocess
import time

import chardet
from PyQt5.QtWidgets import QMessageBox


def decode_output(output_bytes):
    detected_encoding = chardet.detect(output_bytes)['encoding'] or 'utf-8'
    return output_bytes.decode(detected_encoding, errors='replace')


def execute_adb_command(device, command, output_text_widget):
    execution_time = 0
    try:
        output_text_widget.append(f"\nВыполнение '{command}' на устройстве: {device}\n")
        adb_command = f"adb -s {device} {command}"
        
        start_time = time.time()
        
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        
        output_text_widget.append(f"Вывод: {decode_output(output)}\n")
        output_text_widget.append(f"Ошибка: {decode_output(error)}\n")
    except Exception as e:
        
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setText("Произошла ошибка при попытке выполнить ADB команду.")
        error_dialog.setInformativeText(str(e))
        error_dialog.addButton(QMessageBox.Ok)
        error_dialog.exec()
    
    return execution_time
