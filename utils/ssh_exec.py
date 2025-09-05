import os
import subprocess
import sys
import shutil


def _creationflags_no_window() -> int:
    if sys.platform.startswith("win"):
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _find_plink() -> str:
    """
    Ищет plink на всех платформах.
    - Windows: сначала рядом с программой plink.exe, затем в PATH (plink.exe → plink).
    - macOS/Linux: ищет бинарь 'plink' в PATH, также допускает 'plink.exe' если он есть.
    """
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Локально рядом с программой (Windows-вариант)
    local_win = os.path.join(base_dir, "plink.exe")
    if os.path.exists(local_win):
        return local_win

    # Локально рядом с программой (универсальное имя)
    local_unix = os.path.join(base_dir, "plink")
    if os.path.exists(local_unix) and os.access(local_unix, os.X_OK):
        return local_unix

    # В PATH (сначала Windows-имя, затем Unix-имя)
    for name in ("plink.exe", "plink"):
        exe = shutil.which(name)
        if exe:
            return exe

    raise FileNotFoundError(
        "Не найден plink/plink.exe. Установите `brew install putty` (macOS) "
        "или добавьте plink(.exe) в PATH/положите рядом с программой."
    )


def _ensure_remote(remote_argv: list[str]) -> str:
    if not remote_argv or not any(part.strip() for part in remote_argv):
        raise ValueError("Пустая удалённая команда: интерактивная SSH/Plink-сессия запрещена.")
    return " ".join(part for part in remote_argv if part is not None)


def ssh_command(cfg: dict, remote_argv: list[str]) -> list[str]:
    host = cfg["host"]
    port = int(cfg.get("port", 22))
    user = (cfg.get("user") or "admin").strip()
    password = (cfg.get("password") or "").strip()
    hostkey = (cfg.get("hostkey") or "").strip()  # используется только для ветки plink

    remote = _ensure_remote(remote_argv)

    if password:
        # Вариант 2: принудительно используем plink при наличии пароля (кроссплатформенно).
        plink_path = _find_plink()
        cmd = [
            plink_path,
            "-batch",
            "-P", str(port),
            "-l", user,
            "-pw", password,
        ]
        if hostkey:
            cmd += ["-hostkey", hostkey]
        cmd += [host, remote]
        return cmd

    # Без пароля — нативный ssh
    return [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "BatchMode=yes",
        "-o", "NumberOfPasswordPrompts=0",
        "-o", "ConnectTimeout=10",
        f"{user}@{host}",
        remote,
    ]


def ssh_popen(cfg: dict, remote_argv: list[str]) -> subprocess.Popen:
    args = ssh_command(cfg, remote_argv)
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_creationflags_no_window(),
    )
