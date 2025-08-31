from command_runner import command_runner
from webui_logger import log_it
from packaging import version
import socket, requests, re, time, psutil, traceback, platform, textwrap, os, inspect
from config import Globals

class Utils:

    @staticmethod
    def cli_command(command, timeout=120, is_shell_command=False):
        try:
            if is_shell_command:
                exit_code, output = command_runner(command, timeout=timeout, shell=True, method='poller')
            else:
                exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout, method='poller')

            if exit_code == 0:
                log_it("d", f"{command} executed successfully, return code was {exit_code}")
                return output if output else True
            elif exit_code == -254:
                log_it("e", f"{command} timed out.")
                raise TimeoutError(f"Command '{command}' timed out after {timeout} seconds.")
            else:
                log_it("e", f"{command} failed to run successfully, return code was {exit_code}")
                return False
        except TimeoutError as te:
            log_it("e", f"Timeout error while running {command}: {te}")
            raise # re-raise the exception
        except Exception as e:
            log_it("e", f"An error occurred while running {command}: {e}", exc=traceback.format_exc())
        return None

    @staticmethod
    def get_external_ip():
        try:
            log_it("d", "Fetching external IP...")
            response = requests.get('https://api.ipify.org', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
            log_it("e", f"Error fetching IP address from {response.url}, status code: {response.status_code}")
            return "Unable to fetch IP"
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def get_node_pid():
        try:
            log_it("d", "Fetching node PID...")
            if platform.system() == "Linux":
                try:
                    result = Utils.cli_command("pgrep -x cellframe-node", timeout=3, is_shell_command=True)
                    if result:
                        return int(result.strip())
                except Exception as e:
                    log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
                    return None
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                name = proc.info.get('name')
                if name == "cellframe-node":
                    pid = proc.info['pid']
                    log_it("d", f"PID for Cellframe node is {pid}")
                    return pid
            return None
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def get_system_hostname():
        try:
            log_it("d", "Fetching hostname...")
            return socket.gethostname()
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def format_uptime(seconds):
        try:
            log_it("d", "Formatting uptime...")
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 0:
                return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None


    @staticmethod
    def get_sys_stats():
        try:
            PID = Globals.NODE_PID # I can (safely?) assume that this is set by now
            if PID:
                log_it("d", "Fetching system stats...")
                process = psutil.Process(PID)
                sys_stats = {}
                cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count()
                sys_stats['node_cpu_usage'] = cpu_usage

                memory_info = process.memory_info()
                memory_usage_mb = memory_info.rss / 1024 / 1024
                sys_stats['node_memory_usage_mb'] = round(memory_usage_mb, 2)

                create_time = process.create_time()
                uptime_seconds = time.time() - create_time
                sys_stats['node_uptime'] = uptime_seconds

                boot_time = psutil.boot_time()
                system_uptime_seconds = time.time() - boot_time
                sys_stats['system_uptime'] = system_uptime_seconds

                return sys_stats
            return None
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def get_installed_node_version():
        try:
            log_it("d", "Fetching installed node version...")
            version_cmd = Utils.cli_command("version", timeout=5)
            if version_cmd:
                version_match = re.search(r"(\d.+)", version_cmd)
                if version_match:
                    current_version = version_match.group(1).replace("-",".")
                    log_it("d", f"Installed node version: {current_version}")
                    return current_version
                return None
            return None
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def get_latest_node_version():
        try:
            log_it("d", "Fetching latest node version...")
            response = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D", timeout=5)
            if response.status_code == 200:
                matches = re.findall(r"(\d\.\d\-\d+)", response.text)
                if matches:
                    versions = [match.replace("-", ".") for match in matches]
                    latest_version = max(versions, key=version.parse)
                    log_it("d", f"Latest node version: {latest_version}")
                    return latest_version
                return None
            log_it("e", f"Error fetching latest node version from {response.url}, status code: {response.status_code}")
            return None
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def is_running_as_service():
        try:
            log_it("d", "Checking if running as service...")
            if os.environ.get("INVOCATION_ID"):
                log_it("d", "Running as service, INVOCATION_ID found.")
                return True
            return False
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return False

    @staticmethod
    def restart_node():
        try:
            if not Globals.IS_RUNNING_AS_SERVICE:
                log_it("e", "Node is not running as a service, cannot restart.")
                return
            node_pid = Utils.get_node_pid()
            if node_pid:
                proc = psutil.Process(node_pid)
                log_it("d", f"Trying to stop {node_pid}")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    log_it("d", f"Can't terminate {node_pid}, killing it...")
                except psutil.TimeoutExpired:
                    proc.kill()
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    @staticmethod
    def is_port_available(port, host="0.0.0.0"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind((host, port))
                    return True
                except OSError:
                    return False
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return False

    @staticmethod
    def is_cli_ready():
        try:
            log_it("d", "Running version cmd...")
            version_cmd = Utils.cli_command("version", timeout=2)
            if not version_cmd:
                log_it("e", "CLI is not ready, no version command output.")
                return False
            if version_cmd:
                log_it("d", f"Got data from cli, it's ready!")
                return True
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return False

    @staticmethod
    def remove_spacing(text):
        try:
            log_it("d", "Removing extra spacing from text...")
            return textwrap.dedent(text).strip()
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return text

    @staticmethod
    def delay(seconds, logging=True):
        caller = inspect.stack()[1].function
        try:
            if logging:
                log_it("d", f"Delaying for {seconds} seconds... (called from: {caller})")
            time.sleep(seconds)
        except Exception as e:
            log_it("e", f"An error occurred during delay: {e}", exc=traceback.format_exc())

    @staticmethod
    def get_current_script_directory():
        try:
            log_it("d", "Fetching current script directory...")
            return os.path.dirname(os.path.abspath(__file__))
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
            return None

    @staticmethod
    def get_script_parent_directory():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Globals.IS_RUNNING_AS_SERVICE = Utils.is_running_as_service()
Globals.NODE_PID = Utils.get_node_pid()
Globals.CURRENT_NODE_VERSION = Utils.get_installed_node_version()