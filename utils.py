import DAP, socket, requests, re, time, psutil, json, os, time, schedule, inspect, subprocess
from pycfhelpers.node.logging import CFLog
from pycfhelpers.node.net import CFNet
from packaging.version import Version
from collections import OrderedDict
from datetime import datetime
import cachetools.func
from concurrent.futures import ThreadPoolExecutor

log = CFLog()

def getScriptDir():
    return os.path.dirname(os.path.abspath(__file__))

def logNotice(msg):
    func_name = inspect.stack()[1].function
    log.notice(f"{PLUGIN_NAME} [{func_name}] {msg}")

def logError(msg):
    frame_info = inspect.stack()[1]
    func_name = frame_info.function
    file_name = frame_info.filename
    line_number = frame_info.lineno
    
    log_message = f"{PLUGIN_NAME} [{func_name} in {file_name} in line {line_number}] {msg}"
    log.error(log_message)
    try:
        curr_time = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
        with open(os.path.join(getScriptDir(), "error_log.txt"), "a") as f:
            f.write(f"[{curr_time}] {log_message}\n")
    except Exception as e:
        log.error(f"Failed to write to log file: {e}")
    return func_name

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
        manifest_path = os.path.join(getScriptDir(), "manifest.json")
        with open(manifest_path) as manifest:
            data = json.load(manifest)
            curr_version = Version(data["version"])
            logNotice(f"Current plugin version: {curr_version}")
                
        url = "https://raw.githubusercontent.com/hyttmi/cellframe-masternode-webui/refs/heads/master/manifest.json"
        res = requests.get(url).json()
        latest_version = Version(res["version"])
        logNotice(f"Latest plugin version: {latest_version}")
        return curr_version < latest_version, str(curr_version), str(latest_version)
    except Exception as e:
        logError(f"Error: {e}")
        return f"Error: {e}"
    
def CLICommand(command, timeout=60):
    try:
        command_list = ["/opt/cellframe-node/bin/cellframe-node-cli"] + command.split()
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            ret = f"Command {command} failed with error: {result.stderr.strip()}"
            logError(ret)
            return ret
    except subprocess.TimeoutExpired:
        ret = f"Command {command} timed out after {timeout} seconds!"
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
        cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count() # Divide by CPU cores, it's possible that only one core is @ +100%
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
        version = CLICommand("version")
        return version.split()[2].replace("-",".")
    except Exception as e:
        logError(f"Error: {e}")
        return "N/A"

@cachetools.func.ttl_cache(maxsize=10, ttl=7200)
def getLatestNodeVersion():
    try:
        request = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D")
        if request.status_code == 200:
            res = request.text
            match = re.search(r"(\d.\d-\d{3})", res)
            if match:
                return match.group(1).replace("-",".")
        else:
            return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10, ttl=3600)
def getCurrentTokenPrice(token):
    try:
        req = requests.get(f"https://coinmarketcap.com/currencies/{token}/")
        if req.status_code == 200:
            res = req.text
            price_match = re.search(r"price today is \$(\d+.\d+)", res)
            if price_match:
                return price_match.group(1)
            else:
                return None
        else:
            logError(f"Failed to fetch token price for {token}. Request status code: {req.status_code}")
            return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

def getListNetworks():
    try:
        return CFNet.active_nets()
    except Exception as e:
        logError(f"Error retrieving networks: {e}")
        return None

def readNetworkConfig(network):
    try:
        config_file = f"/opt/cellframe-node/etc/network/{network}.cfg"
        with open(config_file, "r") as file:
            text = file.read()
        cert_match = re.search(r"^blocks-sign-cert=(.+)", text, re.MULTILINE)
        wallet_match = re.search(r"^fee_addr=(.+)", text, re.MULTILINE)
        if cert_match and wallet_match:
            net_config = {
                "blocks_sign_cert": cert_match.group(1),
                "wallet": wallet_match.group(1)
            }
            return net_config
        else:
            return None
    except FileNotFoundError:
        logError(f"Configuration file for {network} not found!")
    except Exception as e:
        logError(f"Error: {e}")

def getAutocollectStatus(network):
    autocollect_cmd = CLICommand(f"block autocollect status -net {network} -chain main")
    if "is active" in autocollect_cmd:
        return "Active"
    else:
        return "Inactive"

@cachetools.func.ttl_cache(maxsize=16384, ttl=3600)
def getBlocks(network, cert=None, block_type='all', today=False):
    try:
        if block_type == 'all':
            all_blocks_cmd = CLICommand(f"block count -net {network}")
            logNotice(f"Fetching block count in {network}")
            all_blocks_match = re.search(r":\s+(\d+)", all_blocks_cmd)
            if all_blocks_match:
                return int(all_blocks_match.group(1))
            else:
                return None
        elif block_type == 'first_signed' and cert:
            logNotice(f"Fetching first signed blocks count in {network}")
            cmd_get_first_signed_blocks = CLICommand(f"block list -net {network} first_signed -cert {cert} -limit 1")
            blocks_match = re.search(r"have blocks: (\d+)", cmd_get_first_signed_blocks)
            if blocks_match:
                return int(blocks_match.group(1))
            else:
                return None
        elif block_type == 'signed' and cert:
            logNotice(f"Fetching block list in {network}")
            cmd_output = CLICommand(f"block list -net {network} signed -cert {cert}")
            today_str = datetime.now().strftime("%a, %d %b %Y")
            blocks_signed_per_day = {}
            lines = cmd_output.splitlines()
            for line in lines:
                if "ts_create:" in line:
                    timestamp_str = line.split("ts_create:")[1].strip()[:-6]
                    block_time = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S")
                    block_day = block_time.strftime("%a, %d %b %Y")
                    if block_day not in blocks_signed_per_day:
                        blocks_signed_per_day[block_day] = 1
                    else:
                        blocks_signed_per_day[block_day] += 1
            sorted_dict = dict(OrderedDict(sorted(blocks_signed_per_day.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y"))))
            if today:
                return blocks_signed_per_day.get(today_str, 0)
            else:
                return sorted_dict
        elif block_type == 'all_signed' and cert:
            logNotice(f"Fetching all signed blocks count in {network}")
            cmd_get_all_signed_blocks = CLICommand(f"block list -net {network} signed -cert {cert} -limit 1")
            blocks_match = re.search(r"have blocks: (\d+)", cmd_get_all_signed_blocks)
            if blocks_match:
                return int(blocks_match.group(1))
            else:
                return None
        else:
            return None
    except Exception as e:
        logError(f"Error: {e}")
        return None

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
            if isNodeSynced(network):
                logNotice("Network is probably synced...")
                net_config = readNetworkConfig(network)
                if net_config is not None:
                    logNotice("Caching rewards...")
                    start_time = time.time()
                    cmd_get_tx_history = CLICommand(f"tx_history -addr {net_config['wallet']}")
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
                    logNotice(f"Rewards cached for {network}! It took {elapsed_time:.2f} seconds!")
                else:
                    return None
            else:
                logNotice(f"Node is not synced yet for {network}!")
                return None
    except Exception as e:
        logError(f"Error: {e}")
            
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

def generateNetworkData():
    networks = getListNetworks()
    if networks is not None:
        network_data = {}
        for network in networks:
            net_config = readNetworkConfig(network)  # Just process masternodes. No need to process normal ones
            if net_config is not None:
                network = str(network)
                cert = net_config['blocks_sign_cert']
                wallet = net_config['wallet']
                net_status = CLICommand(f"net -net {network} get status")
                addr_match = re.search(r"([A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*)", net_status)
                state_match = re.search(r"states:\s+current: (\w+)", net_status)
                target_state_match = re.search(r"target: (\w+)", net_status)
                tokens = getRewardWalletTokens(wallet)
                if network == "Backbone":
                    token_price = getCurrentTokenPrice("cellframe")
                elif network == "KelVPN":
                    token_price = getCurrentTokenPrice("kelvpn")

                if state_match and target_state_match:
                    with ThreadPoolExecutor() as executor:
                        futures = {
                            'first_signed_blocks': executor.submit(getBlocks, network, cert=cert, block_type="first_signed"),
                            'all_signed_blocks_dict': executor.submit(getBlocks, network, cert=cert, block_type="signed"),
                            'all_signed_blocks': executor.submit(getBlocks, network, cert=cert, block_type="all_signed"),
                            'all_blocks': executor.submit(getBlocks, network, block_type="all"),
                            'signed_blocks_today': executor.submit(getBlocks, network, cert=cert, block_type="signed", today=True)
                        }
                        network_info = {
                            'state': state_match.group(1),
                            'target_state': target_state_match.group(1),
                            'address': addr_match.group(1) if addr_match else None,
                            'first_signed_blocks': futures['first_signed_blocks'].result(),
                            'all_signed_blocks_dict': futures['all_signed_blocks_dict'].result(),
                            'all_signed_blocks': futures['all_signed_blocks'].result(),
                            'all_blocks': futures['all_blocks'].result(),
                            'signed_blocks_today': futures['signed_blocks_today'].result(),
                            'autocollect_status': getAutocollectStatus(network),
                            'autocollect_rewards': getAutocollectRewards(network),
                            'fee_wallet_tokens': {token[1]: float(token[0]) for token in tokens} if tokens else None,
                            'rewards': readRewards(network),
                            'token_price': float(token_price)
                        }
                    network_data[network] = network_info
        return network_data
    else:
        return None

    
def generateInfo(exclude=None, format_time=True):
    if exclude is None:
        exclude = []
    sys_stats = getSysStats()
    is_update_available, curr_version, latest_version = checkForUpdate()

    info = {
        'plugin_update_available': is_update_available,
        'current_plugin_version': curr_version,
        'latest_plugin_version': latest_version,
        "plugin_name": PLUGIN_NAME,
        "hostname": getHostname(),
        "system_uptime": formatUptime(sys_stats["system_uptime"]) if format_time else sys_stats["system_uptime"],
        "node_uptime": formatUptime(sys_stats["node_uptime"]) if format_time else sys_stats["node_uptime"],
        "node_version": getCurrentNodeVersion(),
        "node_active_threads": getNodeThreadCount(),
        "latest_node_version": getLatestNodeVersion(),
        "node_cpu_utilization": sys_stats["node_cpu_usage"],
        "node_memory_utilization": sys_stats["node_memory_usage_mb"],
        "website_header_text": getConfigValue("webui", "header_text", default=False),
        "website_accent_color": validateHex(getConfigValue("webui", "accent_color", default="B3A3FF")),
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
        logNotice(f"Using {color_str} as the accent color.")
        return color_str
    else:
        logError(f"Not a valid hexadecimal of colour code: {color_str}")
        return "B3A3FF"
