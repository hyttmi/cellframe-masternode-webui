import socket, requests, re, time, psutil, json, os, time, schedule, cachetools.func
from pycfhelpers.node.logging import CFLog
from pycfhelpers.node.net import CFNet
from packaging.version import Version
from collections import OrderedDict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from command_runner import command_runner
from config import Config
from logger import logDebug, logError, logNotice, getScriptDir

log = CFLog()

@logDebug
def checkForUpdate():
    try:
        manifest_path = os.path.join(getScriptDir(), "manifest.json")
        with open(manifest_path) as manifest:
            data = json.load(manifest)
            curr_version = Version(data["version"])
            logNotice(f"Current plugin version: {curr_version}")
        url = "https://raw.githubusercontent.com/hyttmi/cellframe-masternode-webui/refs/heads/master/manifest.json"
        req = requests.get(url, timeout=5).json()
        latest_version = Version(req["version"])
        logNotice(f"Latest plugin version: {latest_version}")
        return curr_version < latest_version, str(curr_version), str(latest_version)
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error: {e}"
    
def CLICommand(command, timeout=120):
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

def getNodeThreadCount():
    try:
        process = psutil.Process(getPID())
        return int(len(process.threads()))
    except Exception as e:
        logError("Error: {e}")

def getHostname():
    return socket.gethostname()

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
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error {e}"

def getCurrentNodeVersion():
    try:
        logNotice("Fetching current node version...")
        version = CLICommand("version")
        return version.split()[2].replace("-",".")
    except Exception as e:
        logError(f"Error: {e}")
        return "N/A"

@cachetools.func.ttl_cache(maxsize=10, ttl=7200)
def getLatestNodeVersion():
    try:
        logNotice("Fetching latest node version...")
        req = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D", timeout=5)
        if req.status_code == 200:
            match = re.search(r"(\d.\d-\d{3})", req.text)
            if match:
                return match.group(1).replace("-",".")
        else:
            return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10, ttl=3600)
def getCurrentTokenPrice(network):
    try:
        logNotice("Fetching token price...")
        if network == "Backbone":
            req = requests.get(f"https://coinmarketcap.com/currencies/cellframe/", timeout=5)
            if req.status_code == 200:
                price_match = re.search(r"price today is \$(\d+.\d+)", req.text)
                if price_match:
                    return float(price_match.group(1))
                else:
                    return None
            else:
                logError(f"Failed to fetch token price from {req.url}")
                return None
        elif network == "KelVPN":
            req = requests.get(f"https://kelvpn.com/about-token", timeout=5)
            if req.status_code == 200:
                price_match =re.search(r"\$(\d+.\d+)", req.text)
                if price_match:
                    return float(price_match.group(1))
                else:
                    return None
            else:
                logError(f"Failed to fetch token price from {req.url}")
                return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

@logDebug
def getListNetworks():
    try:
        nets = CFNet.active_nets()
        if nets:
            return nets
        else:
            logError("Can't get list of networks!")
            return None
    except Exception as e:
        logError(f"Error retrieving networks: {e}")
        return None

@logDebug
def readNetworkConfig(network):
    config_file = f"/opt/cellframe-node/etc/network/{network}.cfg"
    net_config = {}
    try:
        with open(config_file, "r") as file:
            for line in file:
                line = line.strip()
                cert_match = re.search(r"blocks-sign-cert=(.+)", line)
                if cert_match:
                    net_config["blocks_sign_cert"] = cert_match.group(1)
                wallet_match = re.search(r"fee_addr=(.+)", line)
                if wallet_match:
                    net_config["wallet"] = wallet_match.group(1)
                if "blocks_sign_cert" in net_config and "wallet" in net_config:
                    return net_config
            logError(f"Necessary information missing in {config_file}, not a masternode?")
            return None
    except FileNotFoundError:
        logError(f"Configuration file for {network} not found!")
        return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

@logDebug
def getAutocollectStatus(network):
    try:
        autocollect_cmd = CLICommand(f"block autocollect status -net {network} -chain main")
        if "is active" in autocollect_cmd:
            return "Active"
        else:
            return "Inactive"
    except Exception as e:
        logError(f"Error: {e}")

@logDebug
def getNetStatus(network):
    try:
        net_status = CLICommand(f"net -net {network} get status")
        addr_match = re.search(r"([A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*)", net_status)
        state_match = re.search(r"states:\s+current: (\w+)", net_status)
        target_state_match = re.search(r"target: (\w+)", net_status)
        if state_match and addr_match:
            net_status = {
                "state": state_match.group(1),
                "target_state": target_state_match.group(1),
                "address": addr_match.group(1)
            }
            return net_status
        else:
            return None
    except Exception as e:
        logError(f"Error: {e}")

@logDebug
def getRewardWalletTokens(wallet):
    try:
        cmd_get_wallet_info = CLICommand(f"wallet info -addr {wallet}")
        if cmd_get_wallet_info:
            tokens = re.findall(r"coins:\s+([\d.]+)[\s\S]+?ticker:\s+(\w+)", cmd_get_wallet_info)
            return tokens
        else:
            return None
    except Exception as e:
        logError(f"Error: {e}")
    
@logDebug
def getAutocollectRewards(network):
    try:
        net_config = readNetworkConfig(network)
        if net_config is not None:
            cmd_get_autocollect_rewards = CLICommand(f"block -net {network} autocollect status")
            if cmd_get_autocollect_rewards:
                amounts = re.findall(r"profit is (\d+.\d+)", cmd_get_autocollect_rewards)
                if amounts:
                    return sum(float(amount) for amount in amounts)
                else:
                    return None
        else:
            return None
    except Exception as e:
        logError(f"Error: {e}")
        
@logDebug
def isNodeSynced(network):
    try:
        net_status = CLICommand(f"net -net {network} get status")
        match = re.search(r"main:\s*status: synced", net_status)
        if match:
            return True
        else:
            return False
    except Exception as e:
        logError(f"Error: {e}")
    
def cacheRewards():
    try:
        networks = getListNetworks()
        for network in networks:
            net_config = readNetworkConfig(network)
            if net_config is not None:
                if isNodeSynced(network):
                    logNotice("Caching rewards...")
                    start_time = time.time()
                    cmd_get_tx_history = CLICommand(f"tx_history -addr {net_config['wallet']}")
                    rewards = []
                    reward = {}
                    is_receiving_reward = False
                    lines = cmd_get_tx_history.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith("status: ACCEPTED"):
                            if reward and is_receiving_reward:
                                rewards.append(reward)
                            reward = {}
                            is_receiving_reward = False
                            continue
                        if line.startswith("tx_created:"):
                            original_date = line.split("tx_created:")[1].strip()[:-6]
                            reward['tx_created'] = original_date
                            continue
                        if line.startswith("recv_coins:"):
                            reward['recv_coins'] = line.split("recv_coins:")[1].strip()
                            continue
                        if line.startswith("source_address: reward collecting"):
                            is_receiving_reward = True
                            continue
                    if reward and is_receiving_reward:
                        rewards.append(reward)
                    cache_file_path = os.path.join(getScriptDir(), f".{network}_rewards_cache.json")
                    with open(cache_file_path, "w") as f:
                        json.dump(rewards, f, indent=4)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    logNotice(f"Rewards cached for {network}! It took {elapsed_time:.2f} seconds!")
                else:
                    return None
            else:
                logNotice(f"Node is not synced yet for {network}!")
                return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

def cacheBlocks():
    try:
        networks = getListNetworks()
        for network in networks:
            net_config = readNetworkConfig(network)
            if net_config is not None:
                logNotice("Caching blocks...")
                start_time = time.time()

                block_data = {
                    'block_count': 0,
                    'signed_blocks_count': 0,
                    'first_signed_blocks_count': 0,
                    'all_signed_blocks': {}
                }

                with ThreadPoolExecutor() as executor:
                    futures = {
                        'block_count': executor.submit(CLICommand, f"block count -net {network}"),
                        'first_signed_blocks': executor.submit(CLICommand, f"block list -net {network} first_signed -cert {net_config['blocks_sign_cert']} -limit 1"),
                        'signed_blocks': executor.submit(CLICommand, f"block list -net {network} signed -cert {net_config['blocks_sign_cert']}")
                    }

                block_count_result = futures["block_count"].result()
                block_count_match = re.search(r":\s+(\d+)", block_count_result)
                if block_count_match:
                    block_data["block_count"] = int(block_count_match.group(1))

                signed_blocks_result = futures["signed_blocks"].result()
                signed_blocks_match = re.search(r"have blocks: (\d+)", signed_blocks_result)
                if signed_blocks_match:
                    block_data["signed_blocks_count"] = int(signed_blocks_match.group(1))

                first_signed_match = re.search(r"have blocks: (\d+)", futures["first_signed_blocks"].result())
                if first_signed_match:
                    block_data["first_signed_blocks_count"] = int(first_signed_match.group(1))

                blocks_signed_per_day = {}
                lines = signed_blocks_result.splitlines()
                for line in lines:
                    if "ts_create:" in line:
                        timestamp_str = line.split("ts_create:")[1].strip()[:-6]
                        block_time = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S")
                        block_day = block_time.strftime("%a, %d %b %Y")
                        blocks_signed_per_day[block_day] = blocks_signed_per_day.get(block_day, 0) + 1

                sorted_blocks = OrderedDict(sorted(blocks_signed_per_day.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y")))
                block_data["all_signed_blocks"] = sorted_blocks

                cache_file_path = os.path.join(getScriptDir(), f".{network}_blocks_cache.json")
                with open(cache_file_path, "w") as f:
                    json.dump(block_data, f, indent=4)

                elapsed_time = time.time() - start_time
                logNotice(f"Blocks cached for {network}! It took {elapsed_time:.2f} seconds!")
            else:
                logNotice(f"Network config not found for {network}, skipping caching")
                return None
    except Exception as e:
        logError(f"Error: {e}")

@logDebug
def readRewards(network):
    try:
        rewards = {}
        cache_file_path = os.path.join(getScriptDir(), f".{network}_rewards_cache.json")
        with open(cache_file_path) as f:
            data = json.load(f)
            for reward in data:
                date_string = reward['tx_created']
                amount = float(reward['recv_coins'])
                formatted_date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S")
                formatted_date_str = formatted_date.strftime("%a, %d %b %Y")
                
                if formatted_date_str in rewards:
                    rewards[formatted_date_str] += amount
                else:
                    rewards[formatted_date_str] = amount
        sorted_dict = dict(OrderedDict(sorted(rewards.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y"))))
        return sorted_dict
    except FileNotFoundError:
        logError("Rewards file not found!")
        return None
    except Exception as e:
        logError(f"Error reading rewards: {e}")
        return None

@logDebug
def readBlocks(network, block_type='count', today=False):
    cache_file_path = os.path.join(getScriptDir(), f".{network}_blocks_cache.json")
    if not os.path.exists(cache_file_path):
        logError(f"Cache file for network {network} does not exist.")
        return None
    try:
        with open(cache_file_path, "r") as f:
            block_data = json.load(f)
        
        if block_type == "count":
            return block_data["block_count"]

        if block_type == "all_signed_blocks" and today:
            today_str = datetime.now().strftime("%a, %d %b %Y")
            today_count = block_data["all_signed_blocks"].get(today_str, 0)
            return today_count
        
        if block_type == "all_signed_blocks_count":
            return sum(block_data["all_signed_blocks"].values())
        
        if block_type == "all_signed_blocks":
            return block_data["all_signed_blocks"]
        
        if block_type == "first_signed_blocks_count":
            return block_data["first_signed_blocks_count"]

    except Exception as e:
        logError(f"Error reading blocks for network '{network}': {e}")
        return None
    
def sumRewards(network):
    try:
        rewards = readRewards(network)
        if rewards is None:
            return None
        return sum(rewards.values())
    except Exception as e:
        logError(f"Error: {e}")
        return None

@logDebug
def generateNetworkData():
    networks = getListNetworks()
    if networks is not None:
        network_data = {}
        for network in networks:
            net_config = readNetworkConfig(network)
            if net_config is not None: # Just process masternodes. No need to process normal ones
                network = str(network)
                wallet = net_config['wallet']
                tokens = getRewardWalletTokens(wallet)
                net_status = getNetStatus(network)

                with ThreadPoolExecutor() as executor:
                    futures = {
                        'first_signed_blocks': executor.submit(readBlocks, network, block_type="first_signed_blocks_count"),
                        'all_signed_blocks_dict': executor.submit(readBlocks, network, block_type="all_signed_blocks"),
                        'all_signed_blocks': executor.submit(readBlocks, network, block_type="all_signed_blocks_count"),
                        'all_blocks': executor.submit(readBlocks, network, block_type="count"),
                        'signed_blocks_today': executor.submit(readBlocks, network, block_type="all_signed_blocks", today=True),
                        'token_price': executor.submit(getCurrentTokenPrice, network),
                        'rewards': executor.submit(readRewards, network),
                        'all_rewards': executor.submit(sumRewards, network)
                    }
                    network_info = {
                        'state': net_status['state'],
                        'target_state': net_status['target_state'],
                        'address': net_status['address'],
                        'first_signed_blocks': futures['first_signed_blocks'].result(),
                        'all_signed_blocks_dict': futures['all_signed_blocks_dict'].result(),
                        'all_signed_blocks': futures['all_signed_blocks'].result(),
                        'all_blocks': futures['all_blocks'].result(),
                        'signed_blocks_today': futures['signed_blocks_today'].result(),
                        'autocollect_status': getAutocollectStatus(network),
                        'autocollect_rewards': getAutocollectRewards(network),
                        'fee_wallet_tokens': {token[1]: float(token[0]) for token in tokens} if tokens else None,
                        'rewards': futures['rewards'].result(),
                        'all_rewards': futures['all_rewards'].result(),
                        'token_price': futures['token_price'].result()
                    }
                network_data[network] = network_info
            else:
                return None
        return network_data
    else:
        return None

@logDebug
def generateInfo(exclude=None, format_time=True):
    if exclude is None:
        exclude = []
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

    for key in exclude:
        info.pop(key)
    return info

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
        logError(f"Not a valid hexadecimal of colour code: {color_str}")
