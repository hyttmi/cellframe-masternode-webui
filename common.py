try:
    from command_runner import command_runner
    from logger import log_it
    import inspect, os
except ImportError as e:
    log_it("e", f"ImportError: {e}")

def cli_command(command, timeout=120):
    try:
        exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout)
        if exit_code == 0:
            log_it("i", f"{command} executed succesfully...")
            return output.strip()
        log_it("e", f"{command} failed to run succesfully, return code was {exit_code}")
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None
    
def get_current_script_directory():
    return os.path.dirname(os.path.abspath(__file__))