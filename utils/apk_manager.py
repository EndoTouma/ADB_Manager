from utils.adb_executor import execute_adb_command


class APKManager:
    @staticmethod
    def install(device, apk_path, reinstall=False):
        command = f"install {'-r' if reinstall else ''} {apk_path}".strip()
        return execute_adb_command(device, command)

    @staticmethod
    def uninstall(device, package_name):
        command = f"uninstall {package_name}"
        return execute_adb_command(device, command)
