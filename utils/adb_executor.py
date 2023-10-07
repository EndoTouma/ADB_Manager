import subprocess

def execute_adb_command(device, command, output_text):
    output_text.append(f"\nExecuting '{command}' on device: {device}\n")
    adb_command = f"adb -s {device} {command}"
    process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    output_text.append(f"Output: {output.decode()}\n")
    output_text.append(f"Error: {error.decode()}\n")