import os
import shlex
import shutil
import sys
import subprocess
import time
from typing import List, Optional

import chardet
from PyQt6.QtCore import QThread, pyqtSignal


def _decode_bytes(output_bytes: Optional[bytes]) -> str:
    if not output_bytes:
        return ""
    detected = chardet.detect(output_bytes) or {}
    enc = detected.get("encoding") or "utf-8"
    try:
        return output_bytes.decode(enc, errors="replace")
    except Exception:
        return output_bytes.decode("utf-8", errors="replace")


def _adb_exists() -> bool:
    return shutil.which("adb") is not None or os.path.exists(os.path.join(os.getcwd(), "adb.exe"))

def _windows_startupinfo():
    if sys.platform.startswith("win"):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return si
    return None


def _creationflags_no_window() -> int:
    if sys.platform.startswith("win"):
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _build_adb_args(device: str, command) -> List[str]:
    if isinstance(command, list):
        cmd_parts = command
    else:
        command = (command or "").strip()
        try:
            cmd_parts = shlex.split(command, posix=False)
        except ValueError:
            cmd_parts = command.split()

    cmd_parts = [p.strip('"').strip("'") for p in cmd_parts]

    device = (device or "").strip()

    if not cmd_parts:
        return ["adb"]

    verb = cmd_parts[0].lower()
    if verb in ("connect", "disconnect"):
        if len(cmd_parts) == 1 and device:
            return ["adb", verb, device]
        return ["adb"] + cmd_parts

    return ["adb", "-s", device] + cmd_parts

class ADBWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(float, bool)

    def __init__(self, device: str, command: str | list, timeout: float = 120.0, parent=None):
        super().__init__(parent)
        self.device = device
        self.command = command
        self.timeout = timeout
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        if not _adb_exists():
            self.output_signal.emit("ERROR: adb executable not found in PATH.")
            self.finished_signal.emit(0.0, False)
            return

        args = _build_adb_args(self.device, self.command)
        
        if len(args) >= 2 and args[1] == "install":
            apk_path = next((a.strip('"').strip("'") for a in args[2:] if a.lower().endswith(".apk")), None)
            if not apk_path or not os.path.exists(apk_path):
                self.output_signal.emit(f"ERROR: APK file not found: {apk_path or '(none)'}")
                self.finished_signal.emit(0.0, False)
                return

        start_time = time.time()
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                startupinfo=_windows_startupinfo(),
                creationflags=_creationflags_no_window(),
            )
            
            for raw_line in proc.stdout:
                line = _decode_bytes(raw_line.encode() if isinstance(raw_line, str) else raw_line)
                if self._cancel_requested:
                    proc.kill()
                    self.output_signal.emit("Cancelled by user.")
                    self.finished_signal.emit(round(time.time() - start_time, 2), False)
                    return
                self.output_signal.emit(line.rstrip())

            proc.wait(self.timeout)
            success = proc.returncode == 0

        except subprocess.TimeoutExpired:
            self.output_signal.emit(f"ERROR: Timeout after {self.timeout}s")
            success = False
        except Exception as e:
            self.output_signal.emit(f"ERROR: {e}")
            success = False

        self.finished_signal.emit(round(time.time() - start_time, 2), success)
