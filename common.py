from logger import log_it
import os, subprocess

def cli_command(command, timeout=30, is_shell_command=False, retries=3):
    while retries > 0:
        try:
            if is_shell_command:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    text=True,
                    timeout=timeout
                )
            else:
                full_command = f"/opt/cellframe-node/bin/cellframe-node-cli {command}".split()
                result = subprocess.run(
                    full_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout
                )
            if result.returncode == 0:
                log_it("d", f"{command} executed successfully, return code was {result.returncode}")
                return result.stdout.strip() if result.stdout else True
            log_it("e", f"{command} failed to run successfully, return code was {result.returncode}")
            return None
        except subprocess.TimeoutExpired:
            log_it("e", f"Timeout expired for command: {command}")
        except Exception as e:
            log_it("e", f"An error occurred while running the command: {command}", exc=e)
        retries -= 1
        log_it("w", f"Retrying command: {command} ({retries} attempts left)")
    return None

def get_current_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

def get_script_parent_directory():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))