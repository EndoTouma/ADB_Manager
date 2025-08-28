from __future__ import annotations
import os, shlex, re
from datetime import datetime
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal
from utils.ssh_exec import ssh_popen

class SSHCommandThread(QThread):
    command_finished = pyqtSignal(str, str, bool, float)
    command_output = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int)

    def __init__(self, ssh_cfg: dict, device: str, command: str, reinstall: bool = False, parent=None):
        super().__init__(parent)
        self.ssh = ssh_cfg
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
                return

            action = argv[0].lower()
            if action == "install":
                self._handle_install(argv[1:])
            elif action == "uninstall":
                self._handle_uninstall(argv[1:])
            else:
                self._handle_generic(self._split_command(self.command))
        except Exception as e:
            self.command_output.emit(f"ERROR: {e}")
            self.command_finished.emit(self.device, self.command, False, 0.0)

    def _handle_install(self, args: List[str]):
        if not args:
            self._emit_error_and_finish("ERROR: 'install' requires <apk_path>.")
            return
        flags = [a for a in args if a.startswith("-")]
        non_flags = [a for a in args if not a.startswith("-")]
        if not non_flags:
            self._emit_error_and_finish("ERROR: APK path is missing for 'install'.")
            return

        apk_path = os.path.normpath(os.path.expanduser(non_flags[0].strip('"').strip("'")))
        if not os.path.exists(apk_path):
            self._emit_error_and_finish(f"ERROR: APK file not found: {apk_path}")
            return

        remote_tmp = f"/data/local/tmp/{os.path.basename(apk_path)}"
        self._start_time = datetime.now()
        push_proc = ssh_popen(self.ssh, ["adb", "-s", self.device, "push", apk_path, remote_tmp])
        for line in push_proc.stdout:
            if self._requested_cancel:
                push_proc.kill(); self._emit_error_and_finish("Cancelled."); return
            self.command_output.emit(line.strip())
        push_proc.wait()

        reinstall = self._force_reinstall or any(f.lower() == "-r" for f in flags)
        pm = ["adb", "-s", self.device, "shell", "pm", "install"] + (["-r"] if reinstall else []) + [remote_tmp]
        inst_proc = ssh_popen(self.ssh, pm)
        for line in inst_proc.stdout:
            if self._requested_cancel:
                inst_proc.kill(); self._emit_error_and_finish("Cancelled."); return
            self.command_output.emit(line.strip())
            m = re.search(r"(\d+)%", line)
            if m:
                self.progress_signal.emit(self.device, int(m.group(1)))
        inst_proc.wait()
        self.progress_signal.emit(self.device, 100)

        ssh_popen(self.ssh, ["adb", "-s", self.device, "shell", "rm", "-f", remote_tmp]).wait()

        ok = (inst_proc.returncode == 0)
        self._elapsed_time = (datetime.now() - self._start_time).total_seconds()
        self.command_finished.emit(self.device, self.command, ok, self._elapsed_time)

    def _handle_uninstall(self, args: List[str]):
        if not args:
            self._emit_error_and_finish("ERROR: 'uninstall' requires <package_name>.")
            return
        flags = [a for a in args if a.startswith("-")]
        non_flags = [a for a in args if not a.startswith("-")]
        pkg = non_flags[0] if non_flags else ""
        keep = any(f.lower() == "-k" for f in flags)
        cmd = ["adb", "-s", self.device, "uninstall"] + (["-k"] if keep else []) + [pkg]
        proc = ssh_popen(self.ssh, cmd)
        out = []
        for line in proc.stdout:
            if self._requested_cancel:
                proc.kill(); self._emit_error_and_finish("Cancelled."); return
            out.append(line.strip()); self.command_output.emit(line.strip())
        proc.wait()
        ok = (proc.returncode == 0)
        self.command_finished.emit(self.device, self.command, ok, 0.0)

    def _handle_generic(self, argv: List[str]):
        cmd = ["adb", "-s", self.device] + argv
        self._start_time = datetime.now()
        proc = ssh_popen(self.ssh, cmd)
        for line in proc.stdout:
            if self._requested_cancel:
                proc.kill(); self._emit_error_and_finish("Cancelled."); return
            s = (line or "").strip()
            if s: self.command_output.emit(s)
        proc.wait()
        ok = (proc.returncode == 0)
        self._elapsed_time = (datetime.now() - self._start_time).total_seconds()
        self.command_finished.emit(self.device, self.command, ok, self._elapsed_time)
