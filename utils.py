try:
    import socket, requests, re, time, psutil, json, os, time, schedule, cachetools.func
    from packaging.version import Version, parse
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor
    from command_runner import command_runner
    from config import Config
    from logger import log_debug, log_it
except ImportError as e:
    log_it("e", f"ImportError: {e}")

@log_debug
def check_plugin_update():
    try:
        manifest_path = os.path.join(getScriptDir(), "manifest.json")
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
        return f"Error: {e}"
    
def cli_command(command, timeout=120):
    try:
        exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout)
        if exit_code == 0:
            return output.strip()
        else:
            ret = f"Command failed with error: {output.strip()}"
            log_it("i", ret)
            return ret
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def get_node_pid():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == "cellframe-node":
                return proc.info['pid']
    except Exception as e:
        log_it(f"Error: {e}")
        return None

def get_system_hostname():
    return socket.gethostname() or None

def format_uptime(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

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
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")

def get_installed_node_version():
    try:
        log_it("i", "Fetching current node version...")
        version = cli_command("version")
        if version:
            return version.split()[2].replace("-",".")
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")

@cachetools.func.ttl_cache(maxsize=10, ttl=7200)
def get_latest_node_version():
    try:
        log_it("i", "Fetching latest node version...")
        req = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D", timeout=5)
        if req.status_code == 200:
            matches = re.findall(r"(\d\.\d-\d{3})", req.text)
            if matches:
                versions = [match.replace("-", ".") for match in matches]
                latest_version = max(versions, key=parse)
                return latest_version
            else:
                return None
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

@log_debug
def get_reward_wallet_tokens(wallet):
    try:
        cmd_get_wallet_info = cli_command(f"wallet info -addr {wallet}")
        if cmd_get_wallet_info:
            tokens = re.findall(r"coins:\s+([\d.]+)[\s\S]+?ticker:\s+(\w+)", cmd_get_wallet_info)
            return tokens
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")

@log_debug
def generateInfo(format_time=True):
    try:
        sys_stats = getSysStats()
        is_update_available, curr_version, latest_version = checkForUpdate()

        info = {
            'plugin_update_available': is_update_available,
            'current_plugin_version': curr_version,
            'latest_plugin_version': latest_version,
            "plugin_name": Config.PLUGIN_NAME,
            "hostname": getHostname(),
            "system_uptime": formatUptime(sys_stats["system_uptime"]) if format_time else sys_stats["system_uptime"],
            "node_uptime": formatUptime(sys_stats["node_uptime"]) if format_time else sys_stats["node_uptime"],
            "node_version": getCurrentNodeVersion(),
            "node_active_threads": getNodeThreadCount(),
            "latest_node_version": getLatestNodeVersion(),
            "node_cpu_utilization": sys_stats["node_cpu_usage"],
            "node_memory_utilization": sys_stats["node_memory_usage_mb"],
            "website_header_text": Config.HEADER_TEXT,
            "website_accent_color": validateHex(Config.ACCENT_COLOR),
            "networks": generateNetworkData()
        }
        return info
    except Exception as e:
        logError(f"Error: {e}")

def funcScheduler(func, scheduled_time, every_min=False):
    try:
        scheduler = schedule.Scheduler()
        if every_min:
            scheduler.every(every_min).minutes.do(func)
        else:
            scheduler.every().day.at(scheduled_time).do(func)
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except Exception as e:
        logError(f"Error: {e}")
        
def validateTime(str):
    try:
        datetime.strptime(str, "%H:%M")
        return True
    except ValueError as e:
        logError(f"Error: {e}")
        return False

def validateNum(num):
    try:
        int(num)
        return True
    except ValueError:
        logError("{num} is not a valid number")
        return False
    
def validateHex(color_str):
    if re.match(r"([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", color_str):
        return color_str
    else:
        logError(f"Not a valid hexadecimal colour code: {color_str}")
