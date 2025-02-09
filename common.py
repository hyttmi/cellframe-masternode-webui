from command_runner import command_runner
from logger import log_it
import os

def cli_command(command, timeout=120, is_shell_command=False, retries=3):
    while retries > 0:
        try:
            if is_shell_command:
                exit_code, output = command_runner(command, timeout=timeout, shell=True, method='poller')
            else:
                exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout, method='poller')
            if exit_code == 0:
                log_it("d", f"{command} executed successfully, return code was {exit_code}")
                return output if output else True
            elif exit_code == -254:
                log_it("e", f"{command} timed out, retrying...")
            else:
                log_it("e", f"{command} failed to run successfully, return code was {exit_code}")
                return False
        except Exception as e:
            log_it("e", f"An error occurred while running the command: {command}", exc=e)
        retries -= 1
        log_it("e", f"Retrying command: {command} ({retries} attempts left)")
    return None

def get_current_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

def get_script_parent_directory():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))