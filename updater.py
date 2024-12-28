from common import get_current_script_directory, cli_command
from config import Config
from logger import log_it
from packaging import version
from utils import get_node_pid
from telegram import send_telegram_message
from emailer import send_email
import os, requests, inspect, shutil, json, zipfile, psutil 

def check_plugin_update():
    try:
        manifest_path = os.path.join(get_current_script_directory(), "manifest.json")
        with open(manifest_path) as manifest:
            data = json.load(manifest)
            curr_version = version.parse(data['version'])
            curr_version_str = data['version']
            log_it("d", f"Current plugin version: {curr_version_str}")
        url = "https://api.github.com/repos/hyttmi/cellframe-masternode-webui/releases"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            releases = response.json()
            latest_release = None
            for release in releases:
                if Config.DOWNLOAD_PRERELEASES or not release.get('prerelease', False):
                    latest_release = release
                    break
            if latest_release:
                latest_version_str = latest_release['tag_name']
                latest_version = version.parse(latest_version_str)
                download_url = latest_release.get('zipball_url', None)
                log_it("d", f"Latest plugin version: {latest_version_str}")
                plugin_version_data = {
                    'update_available': curr_version < latest_version,
                    'current_version': curr_version_str,
                    'latest_version': latest_version_str,
                    'download_url': download_url
                }
                return plugin_version_data
            else:
                log_it("d", "New release version was not found.")
                return None
        log_it("e", f"Error fetching version data from {response.url}, status code: {response.status_code}")
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def fetch_and_install_plugin_update():
    try:
        log_it("i", "Checking for plugin update...")
        template_dir = os.path.join(get_current_script_directory(), "templates")
        update_path = os.path.join(get_current_script_directory(), ".autoupdater")
        if os.path.exists(update_path):
            shutil.rmtree(update_path)
        update_info = check_plugin_update()
        if not update_info:
            log_it("e", "Failed to fetch plugin update information.")
            return
        if update_info['update_available']:
            log_it("i", f"New version available: {update_info['latest_version']}")
            download_url = update_info.get('download_url')
            if download_url:
                update_path = os.path.join(get_current_script_directory(), ".autoupdater")
                os.makedirs(update_path, exist_ok=True)
                save_path = os.path.join(update_path, "latest_release.zip")
                log_it("i", f"Downloading latest release from {download_url}")
                download_response = requests.get(download_url, stream=True, timeout=10)
                if download_response.status_code == 200:
                    with open(save_path, "wb") as file:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            file.write(chunk)
                    log_it("d", f"Downloaded latest release to {save_path}.")
                    log_it("d", f"Extracting the update to the parent directory.")
                    if os.path.exists(template_dir):
                        try:
                            log_it("d", "Removing old template directory...")
                            shutil.rmtree(template_dir)
                        except Exception as e:
                            log_it("e", f"Failed to remove {template_dir}!")
                    with zipfile.ZipFile(save_path, 'r') as Z:
                        for file in Z.namelist():
                            if not file.endswith('/'):  # Somehow there's no "easy" way to extract just the files out from the zip package?
                                filename = os.path.basename(file)
                                member_path = os.path.join(get_current_script_directory(), filename)
                                with open(member_path, 'wb') as output_file:
                                    output_file.write(Z.read(file))
                    log_it("d", f"Update extracted successfully.")
                    requirements_path = os.path.join(get_current_script_directory(), "requirements.txt")
                    if os.path.exists(requirements_path):
                        log_it("d", f"Installing requirements from {requirements_path}")
                        command = f"/opt/cellframe-node/python/bin/pip3 install -r {requirements_path}"
                        cmd_run_pip = cli_command(command, is_shell_command=True)
                        if cmd_run_pip:
                            log_it("i", "Dependencies successfully installed")
                            node_pid = get_node_pid()
                            if node_pid:
                                if Config.TELEGRAM_STATS_ENABLED:
                                    send_telegram_message(f"Plugin version ({update_info['latest_version']}) has been installed and your node will be restarted.")
                                if Config.EMAIL_STATS_ENABLED:
                                    send_email(f"Plugin version ({update_info['latest_version']}) has been installed and your node will be restarted.")
                                p = psutil.Process(node_pid)
                                log_it("i", "Restarting node...")
                                p.terminate()
                        else:
                            log_it("e", f"Failed to install update!")
                    else:
                        log_it("e", "Requirements not found in the update package?")
                else:
                    log_it("e", f"Failed to download the update file. Status code: {download_response.status_code}")
            else:
                log_it("e", "No download URL found for the latest release.")
        else:
            log_it("i", f"Plugin is up to date.")
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")