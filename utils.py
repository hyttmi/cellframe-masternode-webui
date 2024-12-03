try:
    import socket, requests, re, time, psutil, json, os, time, schedule, cachetools.func
    from packaging.version import Version, parse
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor
    from command_runner import command_runner
    from config import Config
    from logger import log_debug, log_it
    from sysutils import get_current_script_directory
except ImportError as e:
    log_it("e", f"ImportError: {e}")

@log_debug

def get_current_script_directory():
    return os.path.dirname(os.path.abspath(__file__))

def check_plugin_update():
    try:
        manifest_path = os.path.join(get_current_script_directory(), "manifest.json")
        with open(manifest_path) as manifest:
            data = json.load(manifest)
            curr_version = Version(data["version"])
            log_it("i", f"Current plugin version: {curr_version}")
        url = "https://raw.githubusercontent.com/hyttmi/cellframe-masternode-webui/refs/heads/master/manifest.json"
        req = requests.get(url, timeout=5).json()
        latest_version = Version(req["version"])
        log_it("i", f"Latest plugin version: {latest_version}")
        return curr_version < latest_version, str(curr_version), str(latest_version)
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None
    
def cli_command(command, timeout=120):
    try:
        exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout)
        if exit_code == 0:
            log_it("i", f"{command} executed succesfully...")
            return output.strip()
        log_it("e", f"{command} failed to run succesfully, return code was {exit_code}")
        return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def get_node_pid():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == "cellframe-node":
                return proc.info['pid']
        return None
    except Exception as e:
        log_it(f"Error: {e}")
        return None

def get_system_hostname():
    try:
        return socket.gethostname()
    except:
        return None

@log_debug
def get_sys_stats():
    try:
        PID = get_node_pid()
        if PID:
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
        log_it("e", f"Error: {e}")
        return None

def get_installed_node_version():
    try:
        log_it("i", "Fetching current node version...")
        version = cli_command("version")
        if version:
            current_version = version.split()[2].replace("-",".")
            log_it("i", f"Installed node version: {current_version}")
            return current_version
        return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10, ttl=7200)
def get_latest_node_version():
    try:
        log_it("i", "Fetching latest node version...")
        response = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D", timeout=5)
        if response.status_code == 200:
            matches = re.findall(r"(\d\.\d-\d{3})", response.text)
            if matches:
                versions = [match.replace("-", ".") for match in matches]
                latest_version = max(versions, key=parse)
                return latest_version
            return None
        log_it("e", f"Error fetching latest node version from {response.url}, status code: {response.status_code}")
        return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def format_uptime(seconds):
    try:
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None