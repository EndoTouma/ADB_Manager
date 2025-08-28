from __future__ import annotations

import os
import shlex
import subprocess
import re
from typing import List
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal


class CommandThread(QThread):
    command_finished = pyqtSignal(str, str, bool, float)
    command_output = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int)

    def __init__(self, device: str, command: str, reinstall: bool = False, parent=None):
        super().__init__(parent)
        self.device = (device or "").strip()
        self.command = (command or "").strip()
        self._requested_cancel = False
        self._force_reinstall = bool(reinstall)
        self._start_time: datetime | None = None
        self._elapsed_time: float = 0.0
        self._success: bool = False

    def cancel(self):
        self._requested_cancel = True

    @staticmethod
    def _split_command(cmd: str) -> List[str]:
        try:
            return shlex.split(cmd, posix=False)
        except ValueError:
            return cmd.split()

    def _emit_error_and_finish(self, message: str):
        self.command_output.emit(message)
        self.command_finished.emit(self.device, self.command, False, 0.0)

    def run(self):
        try:
            argv = self._split_command(self.command)
            if not argv:
                self._emit_error_and_finish("ERROR: Empty command.")
                self._success = False
                return

            action = argv[0].lower()
            args = argv[1:]

            if action == "install":
                self._handle_install(args)
            elif action == "uninstall":
                self._handle_uninstall(args)
            else:
                self._handle_generic(self._split_command(self.command))

        except Exception as e:
            self.command_output.emit(f"ERROR: {e}")
            self._success = False
            self.command_finished.emit(self.device, self.command, False, 0.0)

    def _handle_install(self, args: List[str]):
        if not args:
            self._emit_error_and_finish("ERROR: 'install' requires <apk_path>.")
            self._success = False
            return

        flags = [a for a in args if a.startswith("-")]
        non_flags = [a for a in args if not a.startswith("-")]
        if not non_flags:
            self._emit_error_and_finish("ERROR: APK path is missing for 'install'.")
            self._success = False
            return

        apk_path = non_flags[0].strip('"').strip("'")
        apk_path = os.path.normpath(os.path.expanduser(apk_path))
        if not os.path.exists(apk_path):
            self._emit_error_and_finish(f"ERROR: APK file not found: {apk_path}")
            self._success = False
            return

        reinstall = self._force_reinstall or any(f.lower() == "-r" for f in flags)

        adb_cmd = ["adb", "-s", self.device, "install"]
        if reinstall:
            adb_cmd.append("-r")
        adb_cmd.append(apk_path)

        self._start_time = datetime.now()

        self.progress_signal.emit(self.device, 0)

        proc = subprocess.Popen(adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        last_percent = -1
        for line in proc.stdout:
            if self._requested_cancel:
                proc.kill()
                self._emit_error_and_finish("Cancelled.")
                self._success = False
                return

            line = (line or "").strip()
            if line:
                self.command_output.emit(line)

            m = re.search(r"(\d+)%", line)
            if m:
                percent = int(m.group(1))
                if percent != last_percent:
                    last_percent = percent
                    self.progress_signal.emit(self.device, percent)
            else:
                if last_percent < 90:
                    last_percent += 5
                    self.progress_signal.emit(self.device, last_percent)

        proc.wait()

        self.progress_signal.emit(self.device, 100)

        self._success = (proc.returncode == 0)
        self._elapsed_time = (datetime.now() - self._start_time).total_seconds()
        self.command_finished.emit(self.device, self.command, self._success, self._elapsed_time)

    def _handle_uninstall(self, args: List[str]):
        if not args:
            self._emit_error_and_finish("ERROR: 'uninstall' requires <package_name>.")
            self._success = False
            return

        flags = [a for a in args if a.startswith("-")]
        non_flags = [a for a in args if not a.startswith("-")]
        package_name = non_flags[0] if non_flags else ""
        if not package_name:
            self._emit_error_and_finish("ERROR: package name is missing for 'uninstall'.")
            self._success = False
            return

        keep_data = any(f.lower() == "-k" for f in flags)

        adb_cmd = ["adb", "-s", self.device, "uninstall"]
        if keep_data:
            adb_cmd.append("-k")
        adb_cmd.append(package_name)

        self._start_time = datetime.now()

        proc = subprocess.Popen(adb_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in proc.stdout:
            if self._requested_cancel:
                proc.kill()
                self._emit_error_and_finish("Cancelled.")
                self._success = False
                return

            line = (line or "").strip()
            if line:
                self.command_output.emit(line)

        proc.wait()

        self._success = (proc.returncode == 0)
        self._elapsed_time = (datetime.now() - self._start_time).total_seconds()
        self.command_finished.emit(self.device, self.command, self._success, self._elapsed_time)

    def _handle_generic(self, argv: List[str]):
        if not argv:
            self._emit_error_and_finish("ERROR: Empty command.")
            self._success = False
            return

        adb_cmd = ["adb", "-s", self.device] + argv

        self._start_time = datetime.now()
        try:
            proc = subprocess.Popen(
                adb_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in proc.stdout:
                if self._requested_cancel:
                    proc.kill()
                    self._emit_error_and_finish("Cancelled.")
                    self._success = False
                    return
                line = (line or "").strip()
                if line:
                    self.command_output.emit(line)

            proc.wait()
            self._success = (proc.returncode == 0)
        except Exception as e:
            self.command_output.emit(f"ERROR: {e}")
            self._success = False

        self._elapsed_time = (datetime.now() - self._start_time).total_seconds()
        self.command_finished.emit(self.device, self.command, self._success, self._elapsed_time)
