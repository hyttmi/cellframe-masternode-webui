from command_runner import command_runner
from logger import log_it
import inspect, os

def cli_command(command, timeout=120, is_shell_command=False):
    try:
        if is_shell_command:
            exit_code, output = command_runner(command, timeout=timeout, shell=True)
            if exit_code == 0:
                log_it("d", f"{command} executed succesfully, return code was {exit_code}")
                return output if output else True
            else:
                log_it("e", f"{command} failed to run succesfully, return code was {exit_code}")
                return False
        else:
            exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout)
            if exit_code == 0:
                log_it("d", f"{command} executed succesfully...")
                return output.strip()
            else:
                log_it("e", f"{command} failed to run succesfully, return code was {exit_code}")
                return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_current_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

def get_script_parent_directory():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))