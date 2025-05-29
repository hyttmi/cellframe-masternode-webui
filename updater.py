from common import get_current_script_directory, get_script_parent_directory, cli_command
from config import Config
from logger import log_it
from packaging import version
from utils import restart_node
from notifications import notify_all
import os, requests, shutil, json, zipfile, traceback

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
        else:
            log_it("e", f"Error fetching version data from {response.url}, status code: {response.status_code}")
            return None
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return None

def install_plugin_update():
    try:
        log_it("i", "Checking for plugin update...")
        update_info = check_plugin_update()
        if not update_info:
            log_it("e", "Failed to fetch plugin update information.")
            return
        if update_info['update_available']:
            log_it("i", f"New version available: {update_info['latest_version']}")
            download_url = update_info.get('download_url')
            if not download_url:
                log_it("e", "No download URL found for the latest release.")
                return
            if download_and_extract_update(download_url):
                requirements_path = os.path.join(get_current_script_directory(), "requirements.txt")
                if os.path.exists(requirements_path):
                    log_it("d", f"Installing requirements from {requirements_path}")
                    command = f"/opt/cellframe-node/python/bin/pip3 install -r {requirements_path}"
                    if cli_command(command, is_shell_command=True):
                        log_it("i", "Dependencies successfully installed")
                        notify_all(f"Plugin version ({update_info['latest_version']}) has been installed and your node ({Config.NODE_ALIAS}) will be restarted.")
                        log_it("i", "Restarting node...")
                        restart_node() # Or maybe not, if it was launched manually... :D
                    else:
                        log_it("e", "Failed to install dependencies!")
                else:
                    log_it("e", "Requirements not found in the update package?")
            else:
                log_it("e", "Failed to download or extract the update.")
        else:
            log_it("i", "Plugin is up to date.")
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

def download_and_extract_update(download_url):
    try:
        update_path = os.path.join(get_current_script_directory(), ".autoupdater")
        if os.path.exists(update_path):
            shutil.rmtree(update_path)
        os.makedirs(update_path, exist_ok=True)
        save_path = os.path.join(update_path, "cellframe-masternode-webui.zip")
        log_it("i", f"Downloading latest release from {download_url}")
        download_response = requests.get(download_url, stream=True, timeout=10)
        if download_response.status_code != 200:
            log_it("e", f"Failed to download update. HTTP status code: {download_response.status_code}")
            return False
        with open(save_path, "wb") as file:
            for chunk in download_response.iter_content(chunk_size=8192):
                file.write(chunk)
        log_it("d", f"Downloaded latest release to {save_path}.")
        log_it("d", "Extracting the update...")
        with zipfile.ZipFile(save_path, 'r') as Z:
            files = Z.namelist()
            top_level_dir = files[0].split('/')[0]
            log_it("d", f"Update top level dir is {top_level_dir}")
            update_dir = os.path.join(update_path, top_level_dir)
            log_it("d", f"Update dir is {update_dir}")
            Z.extractall(update_path)
        destination_path = os.path.join(get_script_parent_directory(), "cellframe-masternode-webui")
        try:
            shutil.copytree(update_dir, destination_path, dirs_exist_ok=True)
            return True
        except Exception as e:
            log_it("e", "Failed to copy update files", exc=e)
            return False
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return False