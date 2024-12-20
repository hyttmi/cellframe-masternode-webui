from common import cli_command
from logger import log_it
from packaging import version
import socket, requests, re, time, psutil, time, cachetools.func, inspect, psutil

def get_external_ip():
    try:
        log_it("d", "Fetching external IP...")
        response = requests.get('https://ifconfig.me/ip', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        log_it("e", f"Error fetching IP address from {response.url}, status code: {response.status_code}")
        return "Unable to fetch IP"
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10)
def get_node_pid():
    try:
        log_it("d", "Fetching node PID...")
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == "cellframe-node":
                pid = proc.info['pid']
                log_it("d", f"PID for Cellframe node is {pid}")
                return pid
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10)
def get_system_hostname():
    try:
        log_it("d", "Fetching hostname...")
        return socket.gethostname()
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
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
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_sys_stats():
    try:
        PID = get_node_pid()
        if PID:
            log_it("d", "Fetching system stats...")
            process = psutil.Process(PID)
            sys_stats = {}
            cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count() # Divide by CPU cores, it's possible that only one core is @ 100%
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
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10)
def get_installed_node_version():
    try:
        log_it("d", "Fetching installed node version...")
        version = cli_command("version", timeout=5)
        if version:
            current_version = version.split()[2].replace("-",".")
            log_it("d", f"Installed node version: {current_version}")
            return current_version
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
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
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None