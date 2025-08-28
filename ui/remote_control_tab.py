from __future__ import annotations

from PyQt6.QtCore import QTimer, QProcess, QProcessEnvironment
from PyQt6.QtWidgets import QMessageBox

from ui.control_tab import ControlTab
from utils.ssh_exec import ssh_popen
from utils.ssh_command_thread import SSHCommandThread
from utils.ssh_logcat_thread import SSHLogcatThread

import socket, shutil

class RemoteControlTab(ControlTab):

    VERBOSE_SSH = False
    
    def _log(self, text: str):
        if getattr(self, "VERBOSE_SSH", False):
            self.append_output(text)

    def __init__(self, ssh_cfg: dict, devices: list[str], commands: list[str], parent=None):
        self.ssh_cfg = dict(ssh_cfg or {})
        super().__init__(devices, commands)

        QTimer.singleShot(0, self.refresh_device_list)
    
    def check_device_status(self):
        import subprocess
        device_status = {}
        connected_devices = []
        try:
            proc = ssh_popen(self.ssh_cfg, ["adb", "devices"])
            out, _ = proc.communicate(timeout=8)
            if proc.returncode != 0:
                raise RuntimeError(out or "adb devices failed")
            
            lines = (out or "").strip().splitlines()
            if lines and lines[0].lower().startswith("list of devices"):
                lines = lines[1:]
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) == 2:
                    dev, st = parts
                    device_status[dev] = st
                    connected_devices.append(dev)
        except subprocess.TimeoutExpired:
            self.append_output("[SSH] 'adb devices' timeout; showing empty list.")
            self.update_device_grid([])
            return
        except Exception as e:
            self.append_output(f"[SSH] devices check failed: {e}")
            self.update_device_grid([])
            return
        
        self.update_device_grid(sorted(set(connected_devices)))
        for checkbox in self.device_checkboxes:
            dev = checkbox.text()
            st = device_status.get(dev, "offline")
            from utils.device_status import update_device_status_ui
            update_device_status_ui(checkbox, st)
    
    def execute_device_command(self, command: str):
        current_text = (command or "").strip()
        if not current_text:
            QMessageBox.warning(self, "Warning", "Please enter/select an ADB command first.")
            return

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output_text.append(f"<strong>{current_text.upper()} COMMAND</strong>: {current_time}\n")

        self.selected_devices_exec = [cb.text() for cb in self.device_checkboxes if cb.isChecked()]
        if not self.selected_devices_exec:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return

        self.is_install_cmd_exec = current_text.lower().startswith("install ")
        self.total_devices_exec = len(self.selected_devices_exec)
        self.completed_devices_exec = 0

        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QProgressDialog
        self.progress_dialog = QProgressDialog(self)
        self.progress_dialog.setWindowTitle(
            f"ADB Manager (SSH) - {'Installing' if self.is_install_cmd_exec else 'Executing'}"
        )
        self.progress_dialog.setLabelText(
            f"{'Installing' if self.is_install_cmd_exec else 'Executing'} on 1 of {self.total_devices_exec}..."
        )
        self.progress_dialog.setCancelButtonText("Cancel")
        self.progress_dialog.setRange(0, 0)
        self.progress_dialog.setMinimumWidth(400)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        self.command_threads = {}
        for device in self.selected_devices_exec:
            th = SSHCommandThread(self.ssh_cfg, device, current_text)
            th.command_output.connect(self.append_output)
            th.command_finished.connect(self._device_finished)
            th.progress_signal.connect(self._update_progress)
            self.command_threads[device] = th
            th.start()

    def start_logcat(self):
        selected_devices = [cb.text() for cb in self.device_checkboxes if cb.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return
        for device in selected_devices:
            if device not in self.logcat_threads:
                logcat_thread = SSHLogcatThread(self.ssh_cfg, device, log_level=(self.selected_log_level or "V"))
                logcat_thread.logcat_output.connect(self.append_logcat_output)
                logcat_thread.finished.connect(self.logcat_finished)
                self.logcat_threads[device] = logcat_thread
                logcat_thread.start()
                self.output_text.append(f"<strong>Started logcat (SSH) for device: {device}</strong>\n")

    def start_logcat_to_file(self):
        selected_devices = [cb.text() for cb in self.device_checkboxes if cb.isChecked()]
        if not selected_devices:
            QMessageBox.warning(self, "Warning", "Please select at least one device.")
            return

        from PyQt6.QtWidgets import QFileDialog
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("Text Files (*.txt);;All Files (*)")
        file_dialog.setDefaultSuffix("txt")
        file_dialog.setWindowTitle("Save Logcat Output")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if not file_path:
                return
            for device in selected_devices:
                if device not in self.logcat_threads:
                    log_level = self.selected_log_level or "V"
                    logcat_thread = SSHLogcatThread(self.ssh_cfg, device, log_level=log_level, output_file=file_path)
                    self.logcat_threads[device] = logcat_thread
                    logcat_thread.finished.connect(self.logcat_finished)
                    logcat_thread.start()
                    self.output_text.append(f"<strong>Started logcat to file (SSH) for device: {device}</strong>\n")
    
    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]
    
    def _start_ssh_tunnel_plink(self, adb_local_port: int, scrcpy_local_port: int, scrcpy_remote_port: int) -> QProcess:
        host = self.ssh_cfg.get("host")
        user = self.ssh_cfg.get("user")
        port = int(self.ssh_cfg.get("port", 22))
        key = self.ssh_cfg.get("keyfile")
        pw = self.ssh_cfg.get("password")
        fpr = self.ssh_cfg.get("hostkey")
        
        args = [
            "-batch", "-ssh", "-N",
            "-L", f"{adb_local_port}:127.0.0.1:5037",
            "-L", f"{scrcpy_local_port}:127.0.0.1:{scrcpy_remote_port}",
            "-P", str(port)
        ]
        if key:
            args += ["-i", key]
        if pw:
            args += ["-pw", pw]
        if fpr:
            args += ["-hostkey", fpr]
        args += [f"{user}@{host}"]
        
        proc = QProcess(self)
        proc.setProgram("plink")
        proc.setArguments(args)
        proc.start()
        return proc
    
    def view_screen_of_selected_devices(self):
        if not shutil.which("plink"):
            QMessageBox.critical(self, "Plink not found", "Не найден plink в PATH.")
            return
        scrcpy_path = shutil.which("scrcpy")
        if not scrcpy_path:
            QMessageBox.critical(self, "scrcpy not found", "На локальной машине не найден scrcpy в PATH.")
            return
        
        selected = self._get_selected_devices()
        if not selected:
            QMessageBox.information(self, "No device selected", "Выберите хотя бы одно устройство.")
            return
        
        adb_local_port = self._find_free_port()
        ssh_adb = self._start_ssh_tunnel_plink(adb_local_port, self._find_free_port(), 27183)
        if not ssh_adb.waitForStarted(4000):
            QMessageBox.critical(self, "SSH tunnel", "Не удалось запустить plink-туннель (ADB).")
            return
        
        env = QProcessEnvironment.systemEnvironment()
        env.insert("ADB_SERVER_SOCKET", f"tcp:127.0.0.1:{adb_local_port}")
        
        self._ssh_scrcpy_processes = [p for p in getattr(self, "_ssh_scrcpy_processes", [])
                                      if p.state() != QProcess.ProcessState.NotRunning]
        
        def _start_scrcpy_tunnel(local_port: int, remote_port: int) -> QProcess:
            host = self.ssh_cfg.get("host")
            user = self.ssh_cfg.get("user")
            port = int(self.ssh_cfg.get("port", 22))
            pw = self.ssh_cfg.get("password")
            fpr = self.ssh_cfg.get("hostkey")
            
            args = ["-batch", "-ssh", "-N",
                    "-L", f"{local_port}:127.0.0.1:{remote_port}",
                    "-P", str(port)]
            if pw:
                args += ["-pw", pw]
            if fpr:
                args += ["-hostkey", fpr]
            args += [f"{user}@{host}"]
            
            proc = QProcess(self)
            proc.setProgram("plink")
            proc.setArguments(args)
            proc.start()
            return proc
        
        device_titles: dict[str, str] = {}
        for dev in selected:
            rc, out, _ = self._plink_exec(["adb", "-s", dev, "shell", "getprop", "ro.product.model"], timeout_ms=6000)
            model = (out or "").strip()
            device_titles[dev] = f"{model} ({dev})" if model else dev
        
        base_x, base_y, step = 40, 40, 40
        
        from PyQt6.QtCore import QTimer
        scrcpy_tunnels: dict[str, QProcess] = {}
        retry_left: dict[str, int] = {dev: 2 for dev in selected}
        
        def maybe_close_all(_code, _status):
            if all(p.state() == QProcess.ProcessState.NotRunning for p in self._ssh_scrcpy_processes):
                for t in scrcpy_tunnels.values():
                    if t.state() != QProcess.ProcessState.NotRunning:
                        t.terminate()
                        t.waitForFinished(1500)
                ssh_adb.terminate()
                ssh_adb.waitForFinished(2000)
        
        def start_one(idx: int, dev: str, delay_ms: int = 0):
            def _do_start():
                remote_port = 27183 + idx
                local_port = self._find_free_port()
                
                tproc = _start_scrcpy_tunnel(local_port, remote_port)
                if not tproc.waitForStarted(4000):
                    QMessageBox.warning(self, "SSH tunnel", f"Не удалось запустить scrcpy-туннель для {dev}.")
                    return
                scrcpy_tunnels[dev] = tproc
                
                p = QProcess(self)
                p.setProcessEnvironment(env)
                p.setProgram(scrcpy_path)
                p.setArguments([
                    "-s", dev,
                    "--port", str(remote_port),
                    "--tunnel-host=127.0.0.1",
                    "--tunnel-port", str(local_port),
                    "--max-size=800",
                    "--max-fps=30",
                    "--video-bit-rate=3M",
                    "--video-buffer=60",
                    "--no-clipboard-autosync",
                    "-V", "error",
                    "--window-title", device_titles.get(dev, dev),
                    "--window-x", str(base_x + step * idx),
                    "--window-y", str(base_y + step * idx),
                ])
                
                def _on_finished(code, status, d=dev):
                    tail = (bytes(p.readAllStandardError()).decode(errors="ignore") +
                            "\n" +
                            bytes(p.readAllStandardOutput()).decode(errors="ignore")).lower()
                    if code != 0 and "connection refused" in tail and retry_left.get(d, 0) > 0:
                        left = retry_left[d] - 1
                        retry_left[d] = left
                        backoff = 700 * (2 - left)
                        QTimer.singleShot(backoff, lambda: start_one(idx, d))
                        return
                    
                    t = scrcpy_tunnels.get(d)
                    if t and t.state() != QProcess.ProcessState.NotRunning:
                        t.terminate()
                        t.waitForFinished(1500)
                    
                    maybe_close_all(code, status)
                
                p.finished.connect(_on_finished)
                p.start()
                if p.waitForStarted(3000):
                    self._ssh_scrcpy_processes.append(p)
                else:
                    if retry_left.get(dev, 0) > 0:
                        left = retry_left[dev] - 1
                        retry_left[dev] = left
                        QTimer.singleShot(1000, lambda: start_one(idx, dev))
                    else:
                        QMessageBox.warning(self, "scrcpy (SSH)", f"Не удалось запустить scrcpy для {dev}.")
            
            if delay_ms > 0:
                QTimer.singleShot(delay_ms, _do_start)
            else:
                _do_start()
        
        for idx, dev in enumerate(selected):
            start_one(idx, dev, delay_ms=600 * idx)
    
    def _plink_exec(self, remote_argv: list[str], timeout_ms: int = 8000) -> tuple[int, str, str]:
        host = self.ssh_cfg.get("host")
        user = self.ssh_cfg.get("user")
        port = int(self.ssh_cfg.get("port", 22))
        pw = self.ssh_cfg.get("password")
        fpr = self.ssh_cfg.get("hostkey")
        
        args = ["-batch", "-ssh", "-P", str(port)]
        if pw:
            args += ["-pw", pw]
        if fpr:
            args += ["-hostkey", fpr]
        args += [f"{user}@{host}"]
        args += remote_argv
        
        p = QProcess(self)
        p.setProgram("plink")
        p.setArguments(args)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        p.start()
        if not p.waitForStarted(4000):
            return 255, "", "plink failed to start"
        p.waitForFinished(timeout_ms)
        rc = p.exitCode()
        out = bytes(p.readAllStandardOutput()).decode(errors="ignore")
        err = bytes(p.readAllStandardError()).decode(errors="ignore")
        return rc, out, err