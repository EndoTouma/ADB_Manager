import subprocess
import time
import chardet
from PyQt5.QtWidgets import QMessageBox


def decode_output(output_bytes):
    """
    Декодирует байтовый вывод в строку, используя определенную или, по умолчанию, 'utf-8' кодировку.

    :param output_bytes: байтовый вывод для декодирования
    :return: декодированная строка
    """
    detected_encoding = chardet.detect(output_bytes)['encoding'] or 'utf-8'
    return output_bytes.decode(detected_encoding, errors='replace')


def execute_adb_command(device, command, output_text_widget):
    """
    Выполняет ADB команду для указанного устройства и отображает вывод в текстовом виджете.

    :param device: устройство, на котором нужно выполнить команду
    :param command: команда ADB для выполнения
    :param output_text_widget: виджет для отображения вывода команды
    :return: время выполнения команды в секундах
    """
    execution_time = 0  # Инициализация переменной времени выполнения
    try:
        # Добавление сообщения о начале выполнения команды в виджет вывода
        output_text_widget.append(f"\nВыполнение '{command}' на устройстве: {device}\n")
        adb_command = f"adb -s {device} {command}"  # Формирование ADB команды
        
        # Засекаем время начала выполнения команды
        start_time = time.time()
        
        # Выполнение ADB команды и получение stdout и stderr
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        
        # Засекаем время окончания выполнения команды и рассчитываем время выполнения
        end_time = time.time()
        execution_time = round(end_time - start_time, 2)
        
        # Отображение вывода команды и ошибок (если они есть)
        output_text_widget.append(f"Вывод: {decode_output(output)}\n")
        output_text_widget.append(f"Ошибка: {decode_output(error)}\n")
    except Exception as e:
        # Вывод окна сообщения об ошибке в случае исключения
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setText("Произошла ошибка при попытке выполнить ADB команду.")
        error_dialog.setInformativeText(str(e))
        error_dialog.addButton(QMessageBox.Ok)
        error_dialog.exec()
    
    # Возвращение времени выполнения команды
    return execution_time
