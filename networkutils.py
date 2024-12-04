try:
    import cachetools.func, re, requests, os, json
    from logger import log_it
    from utils import cli_command
    from sysutils import get_current_script_directory
    from pycfhelpers.node.net import CFNet
    from datetime import datetime
    from collections import OrderedDict
    from wallets import get_reward_wallet_tokens
    from concurrent.futures import ProcessPoolExecutor
except ImportError as e:
    log_it("e", f"ImportError: {e}")

def get_active_networks():
    try:
        nets = CFNet.active_nets()
        if nets:
            return nets
        log_it("e", "Can't get list of networks!")
        return None
    except Exception as e:
        log_it("e", f"Error retrieving networks: {e}")
        return None

def get_network_config(network):
    config_file = f"/opt/cellframe-node/etc/network/{network}.cfg"
    net_config = {}
    try:
        with open(config_file, "r") as file:
            for line in file:
                line = line.strip()
                cert_match = re.search(r"^blocks-sign-cert=(.+)", line)
                if cert_match:
                    net_config["blocks_sign_cert"] = cert_match.group(1)
                wallet_match = re.search(r"^fee_addr=(.{104})", line)
                if wallet_match:
                    net_config["wallet"] = wallet_match.group(1)
                if "blocks_sign_cert" in net_config and "wallet" in net_config:
                    return net_config
            log_it("e", f"Necessary information missing in {config_file}, not a masternode?")
            return None
    except FileNotFoundError:
        log_it("e", f"Configuration file for {network} not found!")
        return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def get_autocollect_status(network):
    try:
        autocollect_cmd = cli_command(f"block autocollect status -net {network} -chain main")
        if "is active" in autocollect_cmd:
            return "Active"
        else:
            return "Inactive"
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None
        
@cachetools.func.ttl_cache(maxsize=10, ttl=3600)
def get_token_price(network):
    try:
        log_it("i", "Fetching token price...")
        if network == "Backbone":
            response = requests.get(f"https://coinmarketcap.com/currencies/cellframe/", timeout=5)
            if response.status_code == 200:
                price_match = re.search(r"price today is \$(\d+.\d+)", response.text)
                if price_match:
                    return float(price_match.group(1))
                return None
            log_it("e", f"Failed to fetch token price from {response.url}")
            return None
        elif network == "KelVPN":
            response = requests.get(f"https://kelvpn.com/about-token", timeout=5)
            if response.status_code == 200:
                price_match =re.search(r"\$(\d+.\d+)", response.text)
                if price_match:
                    return float(price_match.group(1))
                return None
            log_it("e", f"Failed to fetch token price from {response.url}")
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None
        
@cachetools.func.ttl_cache(maxsize=10)
def get_current_stake_value(network):
    try:
        status = get_network_status(network)
        if status:
            addr = status['address']
            list_keys = cli_command(f"srv_stake list keys -net {network}")
            lines = list_keys.splitlines()
            idx = None
            for i, line in enumerate(lines):
                if addr in line:
                    idx = i
                    break
            if idx is None:
                return None  # Address not found?
            while lines[idx].strip() != "": # Search for the emptiness
                idx -= 1
            for line in lines[idx + 1:]:
                if "stake_value:" in line:
                    stake_value = float(re.search(r"[\d.]+", line).group(0))
                    return stake_value
        return None
    except Exception as e:
        log_it("e" f"Error: {e}")
        return None

def get_network_status(network):
    try:
        net_status = cli_command(f"net -net {network} get status")
        addr_match = re.search(r"([A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*::[A-Z0-9]*)", net_status)
        state_match = re.search(r"states:\s+current: (\w+)", net_status)
        target_state_match = re.search(r"target: (\w+)", net_status)
        if state_match and addr_match and target_state_match:
            net_status = {
                "state": state_match.group(1),
                "target_state": target_state_match.group(1),
                "address": addr_match.group(1)
            }
            return net_status
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def get_autocollect_rewards(network):
    try:
        net_config = get_network_config(network)
        if net_config:
            cmd_get_autocollect_rewards = cli_command(f"block -net {network} autocollect status")
            if cmd_get_autocollect_rewards:
                amounts = re.findall(r"profit is (\d+.\d+)", cmd_get_autocollect_rewards)
                if amounts:
                    return sum(float(amount) for amount in amounts)
                else:
                    return None
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None
        
def get_node_dump(network):
    try:
        cmd_get_node_dump = cli_command(f"node dump -net {network}")
        if cmd_get_node_dump:
            return cmd_get_node_dump
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def get_is_node_synced(network):
    try:
        net_status = cli_command(f"net -net {network} get status")
        match = re.search(r"main:\s*status: synced", net_status)
        if match:
            return True
        else:
            return False
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def get_total_rewards(network, total_sum=False):
    try:
        rewards = {}
        cache_file_path = os.path.join(get_current_script_directory(), f".{network}_rewards_cache.json")
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
        if not total_sum:
            return sorted_dict
        else:
            return sum(rewards.values())
    except FileNotFoundError:
        log_it("e", "Rewards file not found!")
        return None
    except Exception as e:
        log_it("e", f"Error reading rewards: {e}")
        return None

def get_blocks(network, block_type="count", today=False):
    cache_file_path = os.path.join(get_current_script_directory, f".{network}_blocks_cache.json")
    if not os.path.exists(cache_file_path):
        log_it("e", f"Cache file for network {network} does not exist.")
        return None
    try:
        with open(cache_file_path, "r") as f:
            block_data = json.load(f)
        
        if block_type == "count":
            return block_data['block_count']

        if block_type == "all_signed_blocks" and today:
            today_str = datetime.now().strftime("%a, %d %b %Y")
            today_count = block_data["all_signed_blocks"].get(today_str, 0)
            return today_count
        
        if block_type == "all_signed_blocks_count":
            return sum(block_data['all_signed_blocks'].values())
        
        if block_type == "all_signed_blocks":
            return block_data['all_signed_blocks']
        
        if block_type == "first_signed_blocks_count":
            return block_data['first_signed_blocks_count']

    except Exception as e:
        log_it("e", f"Error reading blocks for network '{network}': {e}")
        return None