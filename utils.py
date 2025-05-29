from common import cli_command
from logger import log_it
from packaging import version
import socket, requests, re, time, psutil, time, traceback, platform

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

def get_node_pid():
    try:
        log_it("d", "Fetching node PID...")
        if platform.system() == "Linux":
            result = cli_command("pgrep -x cellframe-node", timeout=3, is_shell_command=True)
            if result:
                return int(result.strip())
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            name = proc.info.get('name')
            if name == "cellframe-node":
                pid = proc.info['pid']
                log_it("d", f"PID for Cellframe node is {pid}")
                return pid
        return None
    except Exception as e:
        log_it("e", f"An error occurred: {e}")
        return None

def get_system_hostname():
    try:
        log_it("d", "Fetching hostname...")
        return socket.gethostname()
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return None

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

def get_sys_stats():
    try:
        PID = get_node_pid()
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

def get_installed_node_version():
    try:
        log_it("d", "Fetching installed node version...")
        version_cmd = cli_command("version", timeout=5)
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

def get_latest_node_version():
    try:
        log_it("d", "Fetching latest node version...")
        response = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D", timeout=5)
        if response.status_code == 200:
            matches = re.findall(r"(\d\.\d-\d{3})", response.text)
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

def restart_node():
    try:
        node_pid = get_node_pid()
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

def is_cli_ready():
    try:
        version_cmd = cli_command("version", timeout=2)
        log_it("d", "Running version cmd...")
        if version_cmd:
            log_it("d", f"Got data from cli, it's ready!")
            return True
        log_it("d", f"No data from CLI!")
        return False
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())