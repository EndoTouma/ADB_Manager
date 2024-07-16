import subprocess
from PyQt6.QtGui import QPalette, QColor


def update_device_status_ui(checkbox, status):
    palette = QPalette()
    if status == "device":
        palette.setColor(QPalette.ColorRole.WindowText, QColor('green'))
    elif status == "offline":
        palette.setColor(QPalette.ColorRole.WindowText, QColor('red'))
    else:
        palette.setColor(QPalette.ColorRole.WindowText, QColor('black'))
    checkbox.setPalette(palette)


def get_device_status():
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    device_lines = result.stdout.strip().split("\n")[1:]  # пропускаем первую строку заголовка
    device_status = {}
    devices = []
    for line in device_lines:
        if line.strip():  # игнорируем пустые строки
            parts = line.split("\t")
            if len(parts) == 2:
                device, status = parts
                device_status[device] = status
                devices.append(device)
    return device_status, devices


