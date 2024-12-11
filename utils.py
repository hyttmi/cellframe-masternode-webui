from command_runner import command_runner
from common import cli_command, get_current_script_directory
from config import Config
from logger import log_it
from packaging import version
import socket, requests, re, time, psutil, json, os, time, cachetools.func, inspect, zipfile, shutil, stat

def check_plugin_update():
    try:
        manifest_path = os.path.join(get_current_script_directory(), "manifest.json")
        with open(manifest_path) as manifest:
            data = json.load(manifest)
            curr_version = version.parse(data['version'])
            curr_version_str = data['version']
            log_it("d", f"Current plugin version: {curr_version_str}")
        url = "https://api.github.com/repos/hyttmi/cellframe-masternode-webui/releases/latest"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            ver_json = response.json()
            latest_version_str = ver_json['tag_name']
            latest_version = version.parse(ver_json['tag_name'])
            log_it("d", f"Latest plugin version: {latest_version_str}")
            plugin_version_data = {
                'update_available': curr_version < latest_version,
                'current_version': curr_version_str,
                'latest_version': latest_version_str
            }
            return plugin_version_data
        log_it("e", f"Error fetching version data from {response.url}, status code: {response.status_code}")
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def fetch_and_install_plugin_update():
    try:
        if Config.AUTO_UPDATE:
            update_path = os.path.join(get_current_script_directory(), ".autoupdater")
            if os.path.exists(update_path):
                shutil.rmtree(update_path)
            update_info = check_plugin_update()
            if not update_info:
                log_it("e", "Failed to fetch plugin update information.")
                return
            if update_info['update_available']:
                log_it("i", f"New version available: {update_info['latest_version']}")
                response = requests.get("https://api.github.com/repos/hyttmi/cellframe-masternode-webui/releases/latest", timeout=5)
                if response.status_code == 200:
                    latest_release = response.json()
                    download_url = latest_release['zipball_url'] if latest_release['zipball_url'] else None
                    if download_url:
                        download_path = os.path.join(update_path)
                        os.makedirs(download_path, exist_ok=True)
                        save_path = os.path.join(download_path, "latest_release.zip")
                        log_it("i", f"Downloading latest release from {download_url}")
                        download_response = requests.get(download_url, stream=True, timeout=10)
                        if download_response.status_code == 200:
                            with open(save_path, "wb") as file:
                                for chunk in download_response.iter_content(chunk_size=8192):
                                    file.write(chunk)
                            log_it("d", f"Downloaded latest release to {save_path}.")
                            log_it("d", f"Extracting the update to the parent directory.")
                            with zipfile.ZipFile(save_path, 'r') as Z:
                                for file in Z.namelist():
                                    if not file.endswith('/'): # Somehow there's no "easy" way to extract just the files out from the zip package?
                                        filename = os.path.basename(file)
                                        member_path = os.path.join(get_current_script_directory(), filename)
                                        with open(member_path, 'wb') as output_file:
                                            output_file.write(Z.read(file))
                            log_it("d", f"Update extracted successfully.")
                            requirements_path = os.path.join(get_current_script_directory(), "requirements.txt")
                            if os.path.exists(requirements_path):
                                pip = f"/opt/cellframe-node/python/bin/pip3"
                                if os.path.exists(pip):
                                    if not os.access(pip, os.X_OK):
                                        log_it("i", "pip3 not executable, making it executable.")
                                        st = os.stat(pip)
                                        os.chmod(pip, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                                    log_it("i", f"Installing requirements from {requirements_path}")
                                    command = f"/opt/cellframe-node/python/bin/pip3 install -r {requirements_path}"
                                    output = cli_command(command, is_shell_command=True)
                                    if output:
                                        log_it("i", "Dependencies succefully installed")
                                else:
                                    log_it("e", "pip3 binary not found!")
                            else:
                                log_it("e", "Requirements not found in the update package?")
                        else:
                            log_it("e", f"Failed to download the update file. Status code: {download_response.status_code}")
                    else:
                        log_it("e", "No download URL found for the latest release.")
                else:
                    log_it("e", f"Error fetching release details. Status code: {response.status_code}")
            else:
                log_it("i", f"Plugin is up to date.")
        else:
            log_it("i", "Automatic updater is disabled.")
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")

@cachetools.func.ttl_cache(maxsize=10)
def get_external_ip():
    try:
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
        return socket.gethostname()
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
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
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

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
                log_it("d", f"Installed node version: {latest_version}")
                return latest_version
            return None
        log_it("e", f"Error fetching latest node version from {response.url}, status code: {response.status_code}")
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None
    

