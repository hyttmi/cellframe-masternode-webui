import inspect
import DAP
from pycfhelpers.node.logging import CFLog
from pycfhelpers.node.net import CFNet
from pycfhelpers.node.types import CFNetState
from command_runner import command_runner
from packaging.version import Version

import socket, requests, re, time, psutil, json, os, time, schedule
from datetime import datetime, timedelta

log = CFLog()

def getScriptDir():
    return os.path.dirname(os.path.abspath(__file__))

def logNotice(msg):
    func_name = inspect.stack()[1].function
    log.notice(f"{PLUGIN_NAME} [{func_name}] {msg}")

def logError(msg):
    func_name = inspect.stack()[1].function
    log.error(f"{PLUGIN_NAME} [{func_name}] {msg}")

def getConfigValue(section, key, default=None):
    try:
        value = DAP.configGetItem(section, key)
        return value
    except ValueError:
        return default

PLUGIN_NAME = "Cellframe system & node info by Mika H (@CELLgainz)"
PLUGIN_URI = getConfigValue("webui", "uri", default="webui")
    
def checkForUpdate():
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(f"{dir_path}/manifest.json") as manifest:
            data = json.load(manifest)
            curr_version = Version(data["version"])
            logNotice(f"Current plugin version: {curr_version}")
                
        url = "https://raw.githubusercontent.com/hyttmi/cellframe-masternode-webui/refs/heads/master/manifest.json"
        res = requests.get(url).json()
        latest_version = Version(res["version"])
        logNotice(f"Latest plugin version: {latest_version}")
        return curr_version < latest_version, curr_version, latest_version
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error: {e}"
    
def CLICommand(command, timeout=5):
    try:
        exit_code, output = command_runner(f"/opt/cellframe-node/bin/cellframe-node-cli {command}", timeout=timeout)
        if exit_code == 0:
            return output.strip()
        else:
            ret = f"Command failed with error: {output.strip()}"
            logError(ret)
            return ret
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error: {e}"

def getPID():
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == "cellframe-node":
                return proc.info['pid']
        return None
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error: {e}"

def getHostname():
    return socket.gethostname()

def getExtIP():
    try:
        res = requests.get('https://ifconfig.me/ip')
        return res.text
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error: {e}"

def formatUptime(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def getSysStats():
    try:
        PID = getPID()
        process = psutil.Process(PID)
        sys_stats = {}
        cpu_usage = process.cpu_percent(interval=1)
        sys_stats['node_cpu_usage'] = cpu_usage if cpu_usage is not None else "N/A"

        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / 1024 / 1024
        sys_stats['node_memory_usage_mb'] = round(memory_usage_mb, 2) if memory_usage_mb is not None else "N/A"
        
        create_time = process.create_time()
        uptime_seconds = time.time() - create_time
        sys_stats['node_uptime'] = formatUptime(uptime_seconds) if uptime_seconds is not None else "N/A"

        boot_time = psutil.boot_time()
        system_uptime_seconds = time.time() - boot_time
        sys_stats['system_uptime'] = formatUptime(system_uptime_seconds) if system_uptime_seconds is not None else "N/A"

        return sys_stats
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error {e}"

def getCurrentNodeVersion():
    version = CLICommand("version")
    return version.split()[2].replace("-",".")

def getLatestNodeVersion():
    badge_url = "https://pub.cellframe.net/linux/cellframe-node/master/node-version-badge.svg"
    res = requests.get(badge_url).text
    version_pattern = r'>(\d.\d.\d+)'
    match = re.search(version_pattern, res)
    if match:
        latest_version = match.group(1)
        return latest_version
    else:
        return "N/A"

def getListNetworks():
    try:
        return CFNet.active_nets()
    except Exception as e:
        logError(f"Error retrieving networks: {e}")
        return None

def readNetworkConfig(network):
    net_config = []
    config_file = f"/opt/cellframe-node/etc/network/{network}.cfg"
    with open(config_file, "r") as file:
        text = file.read()
    pattern_cert = r"^blocks-sign-cert=(.+)"
    pattern_wallet = r"^fee_addr=(.+)"
    cert_match = re.search(pattern_cert, text, re.MULTILINE)
    wallet_match = re.search(pattern_wallet, text, re.MULTILINE)
    if cert_match and wallet_match:
        net_config.append(cert_match.group(1))
        net_config.append(wallet_match.group(1))
        return net_config
    else:
        return None

def getAutocollectStatus(network):
    autocollect_cmd = CLICommand(f"block autocollect status -net {network} -chain main")
    if not "is active" in autocollect_cmd:
        return "Inactive"
    else:
        return "Active"

def getAllBlocks(network):
    all_blocks_cmd = CLICommand(f"block count -net {network}")
    pattern_all_blocks = r":\s+(\d+)"
    all_blocks_match = re.search(pattern_all_blocks, all_blocks_cmd)
    if all_blocks_match:
        return all_blocks_match.group(1)
    else:
        return None

def getFirstSignedBlocks(network):
    net_config = readNetworkConfig(network)
    if net_config is not None:
        cmd_get_first_signed_blocks = CLICommand(f"block list -net {network} chain -main first_signed -cert {net_config[0]} -limit 1")
        pattern = r"have blocks: (\d+)"
        blocks_match = re.search(pattern, cmd_get_first_signed_blocks)
        if blocks_match:
            result = blocks_match.group(1)
            return result
    else:
        return None

def getAllSignedBlocks(network):
    net_config = readNetworkConfig(network)
    if net_config is not None:
        cmd_get_all_signed_blocks = CLICommand(f"block list -net {network} chain -main signed -cert {net_config[0]} -limit 1")
        pattern = r"have blocks: (\d+)"
        blocks_match = re.search(pattern, cmd_get_all_signed_blocks)
        if blocks_match:
            result = blocks_match.group(1)
            return result
    else:
        return None

def getSignedBlocksToday(network):
    net_config = readNetworkConfig(network)
    if net_config is not None:
        cmd_output = CLICommand(f"block list -net {network} signed -cert {net_config[0]}")
        today_str = datetime.now().strftime("%a, %d %b %Y")
        blocks_signed_today = 0
        lines = cmd_output.splitlines()
        for line in lines:
            if "ts_create:" in line and today_str in line:
                blocks_signed_today += 1
        return blocks_signed_today
    else:
        return None

def getSignedBlocksLast7Days(network):
    net_config = readNetworkConfig(network)
    if net_config is not None:
        cmd_output = CLICommand(f"block list -net {network} signed -cert {net_config[0]}")
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        
        blocks_signed_per_day = { 
            (today - timedelta(days=i)).strftime("%a, %d %b %Y"): 0 
            for i in range(7)
        }
        
        lines = cmd_output.splitlines()
        for line in lines:
            if "ts_create:" in line:
                timestamp_str = line.split("ts_create:")[1].strip()
                timestamp_str = timestamp_str.rsplit(' ', 1)[0]
                block_time = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S")
                
                if seven_days_ago <= block_time <= today:
                    block_day = block_time.strftime("%a, %d %b %Y")
                    if block_day in blocks_signed_per_day:
                        blocks_signed_per_day[block_day] += 1

        return blocks_signed_per_day
    else:
        return None

def getRewardWalletTokens(network):
    net_config = readNetworkConfig(network)
    if net_config is not None:
        cmd_get_wallet_info = CLICommand(f"wallet info -addr {net_config[1]}")
        if cmd_get_wallet_info:
            balance_pattern = r"coins:\s+([\d.]+)[\s\S]+?ticker:\s+(\w+)"
            tokens = re.findall(balance_pattern, cmd_get_wallet_info)
            return tokens
    else:
        return None
    
def getAutocollectRewards(network):
    net_config = readNetworkConfig(network)
    if net_config is not None:
        cmd_get_autocollect_rewards = CLICommand(f"block -net {network} autocollect status")
        if cmd_get_autocollect_rewards:
            amount_pattern = r"profit is (\d+.\d+)"
            amounts = re.findall(amount_pattern, cmd_get_autocollect_rewards)
            total_amount = sum(float(amount) for amount in amounts)
            return total_amount
    else:
        return None
    
def cacheRewards():
    while True:
        try:
            networks = getListNetworks()
            for network in networks:
                net_config = readNetworkConfig(network)
                if net_config is not None:
                    logNotice("Caching rewards...")
                    start_time = time.time()
                    wallet = net_config[1]
                    cmd_get_tx_history = CLICommand(f"tx_history -addr {wallet}", timeout=60)
                    rewards = []
                    reward = {}
                    is_receiving_reward = False
                    lines = cmd_get_tx_history.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith("status: ACCEPTED"):  # OK, we have ACCEPTED status
                            if reward and is_receiving_reward:
                                rewards.append(reward)
                            reward = {}
                            is_receiving_reward = False
                        if line.startswith("tx_created:"):
                            original_date = line.split("tx_created:")[1].strip()[:-6]
                            reward['tx_created'] = original_date
                        if line.startswith("recv_coins:"):
                            reward['recv_coins'] = line.split("recv_coins:")[1].strip()
                        if line.startswith("source_address: reward collecting"):
                            is_receiving_reward = True
                    if reward and is_receiving_reward:
                        rewards.append(reward)
                    cache_file_path = os.path.join(getScriptDir(), f".{network}_rewards_cache.txt")
                    with open(cache_file_path, "w") as f:
                        for reward in rewards:
                            f.write(f"{reward['tx_created']}|{reward['recv_coins']}\n")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    logNotice(f"Rewards cached! It took {elapsed_time:.2f} seconds!")
                    time.sleep(1800)  # TODO: Implement different way to this
                else:
                    return None
        except Exception as e:
            logError(f"Error caching rewards: {e}")
            
def readRewards(network):
    try:
        rewards = {}
        with open(os.path.join(getScriptDir(), f".{network}_rewards_cache.txt")) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                date_string, amount = line.split("|")
                amount = float(amount)
                today = datetime.now()
                seven_days_ago = today - timedelta(days=7)
                formatted_date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S") # First to object...
                formatted_date_str = formatted_date.strftime("%a, %d %b %Y")
                if seven_days_ago <= formatted_date <= today:
                    if formatted_date_str in rewards:
                        rewards[formatted_date_str] += amount
                    else:
                        rewards[formatted_date_str] = amount
        return rewards
    except FileNotFoundError:
        logError("Rewards file not found!")
        return None
    except Exception as e:
        logError(f"Error reading rewards: {e}")
        return None
                

def generateNetworkData():
    networks = getListNetworks()
    if networks is not None:
        network_data = []
        for network in networks:
            net_status = CLICommand(f"net -net {network} get status")
            addr_pattern = r"([A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*)"
            state_pattern = r"states:\s+current: (\w+)"
            target_state_pattern = r"target: (\w+)"
            addr_match = re.search(addr_pattern, net_status)
            state_match = re.search(state_pattern, net_status)
            target_state_match = re.search(target_state_pattern, net_status)
            tokens = getRewardWalletTokens(network)
            
            if state_match and target_state_match:
                network_info = {
                    'name': network,
                    'state': state_match.group(1),
                    'target_state': target_state_match.group(1),
                    'address': addr_match.group(1),
                    'first_signed_blocks': getFirstSignedBlocks(network),
                    'all_signed_blocks': getAllSignedBlocks(network),
                    'all_blocks': getAllBlocks(network),
                    'signed_blocks_today': getSignedBlocksToday(network),
                    'signed_blocks_last_7_days': getSignedBlocksLast7Days(network),
                    'autocollect_status': getAutocollectStatus(network),
                    'autocollect_rewards': getAutocollectRewards(network),
                    'fee_wallet_tokens': [{'token': token[1], 'balance': token[0]} for token in tokens] if tokens else None,
                    'rewards': readRewards(network)
                }
                network_data.append(network_info)
            else:
                return None
        return network_data
    else:
        return None
    
def funcScheduler(func, scheduled_time):
    try:
        scheduler = schedule.Scheduler()
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