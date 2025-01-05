from common import cli_command, get_current_script_directory
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logger import log_it
from pycfhelpers.node.net import CFNet
import re, requests, os, json, inspect, cachetools.func

@cachetools.func.ttl_cache(maxsize=10)
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

@cachetools.func.ttl_cache(maxsize=10)
def get_network_config(network):
    network_config_file = f"/opt/cellframe-node/etc/network/{network}.cfg"
    net_config = {}
    try:
        with open(network_config_file, "r") as file:
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
            log_it("e", f"Necessary information missing in {network_config_file}, not a masternode?")
            return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_autocollect_status(network):
    try:
        autocollect_status = {}
        autocollect_cmd = cli_command(f"block autocollect status -net {network}")
        amounts = re.findall(r"profit is (\d+.\d+)", autocollect_cmd)
        if amounts:
            autocollect_status['rewards'] = sum(float(amount) for amount in amounts)
        else:
            autocollect_status['rewards'] = 0
        autocollect_status['active'] = "Active" if "is active" in autocollect_cmd else "Inactive"
        if autocollect_status:
            return autocollect_status
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

@cachetools.func.ttl_cache(maxsize=10)
def get_current_block_reward(network):
    try:
        block_reward_cmd = cli_command(f"block reward show -net {network}")
        if block_reward_cmd:
            block_reward_match = re.search(r"(\d+.\d+)", block_reward_cmd)
            if block_reward_match:
                return float(block_reward_match.group(1))
            return None
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_token_price(network):
    try:
        network = str(network).lower()
        log_it("d", "Fetching token price...")
        if network == "backbone":
            response = requests.get(f"https://coinmarketcap.com/currencies/cellframe/", timeout=5)
            if response.status_code == 200:
                price_match = re.search(r"price today is \$(\d+.\d+)", response.text)
                if price_match:
                    return float(price_match.group(1))
                return None
            log_it("e", f"Failed to fetch token price from {response.url}")
            return None
        elif network == "kelvpn":
            response = requests.get(f"https://kelvpn.com/about-token", timeout=5)
            if response.status_code == 200:
                price_match =re.search(r"\$(\d+.\d+)", response.text)
                if price_match:
                    return float(price_match.group(1))
                return None
            log_it("e", f"Failed to fetch token price from {response.url}")
            return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_node_data(network):
    try:
        status = get_network_status(network)
        if status:
            addr = status['address']
            list_keys = cli_command(f"srv_stake list keys -net {network}")
            total_weight_in_network = re.search(r"total_weight_coins:\s+(\d+\.\d+)", list_keys)
            total_weight = float(total_weight_in_network.group(1))
            pattern = re.compile(
                r'pkey_hash:\s+(?P<pkey_hash>\w+)\s+'
                r'stake_value:\s+(?P<stake_value>\d+\.\d+)\s+'
                r'effective_value:\s+(?P<effective_value>\d+\.\d+)\s+'
                r'related_weight:\s+(?P<related_weight>\d+\.\d+)\s+'
                r'tx_hash:\s+(?P<tx_hash>\w+)\s+'
                r'node_addr:\s+(?P<node_addr>[A-Z0-9]+::[A-Z0-9]+::[A-Z0-9]+::[A-Z0-9]+)\s+'
                r'sovereign_addr:\s+(?P<sovereign_addr>\w+)\s+'
                r'sovereign_tax:\s+(?P<sovereign_tax>\d+\.\d+)\s+'
                r'active:\s+(?P<active>true|false)'
            ) # Compiling regex makes it much faster for this
            active_nodes_count = len(re.findall(r"active: true", list_keys))
            nodes = []
            for match in pattern.finditer(list_keys):
                node = match.groupdict()
                node['is_my_node'] = (node['node_addr'] == addr) # This is our node
                node['is_sovereign'] = float(node['sovereign_tax']) > 0.0 # If bigger than 0.0, it's a sovereign node
                nodes.append(node)

            info = {
                'active_nodes_count': active_nodes_count,
                'total_weight': total_weight
            }
            result = {
                'info': info,
                'nodes': nodes
            }
            log_it("d", result)
            return result
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_network_status(network):
    try:
        net_status = cli_command(f"net -net {network} get status")
        addr_match = re.search(r"([A-Z0-9]+::[A-Z0-9]+::[A-Z0-9]+::[A-Z0-9]+)", net_status)
        state_match = re.search(r"states:\s+current: (\w+)", net_status)
        target_state_match = re.search(r"target: (\w+)", net_status)
        if state_match and addr_match and target_state_match:
            net_status = {
                "state": state_match.group(1),
                "target_state": target_state_match.group(1),
                "address": addr_match.group(1)
            }
            return net_status
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_node_dump(network):
    try:
        cmd_get_node_dump = cli_command(f"node dump -net {network}")
        if cmd_get_node_dump:
            lines = cmd_get_node_dump.splitlines()
            return "\n".join(lines[:-1])
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_rewards(network, total_sum=False, rewards_today=False):
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
            sorted_dict = dict(sorted(rewards.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y")))
            if total_sum:
                return sum(rewards.values())
            elif rewards_today:
                today_str = datetime.now().strftime("%a, %d %b %Y")
                return rewards.get(today_str, None)
            else:
                return sorted_dict
        return None
    except FileNotFoundError:
        log_it("e", "Rewards file not found!")
        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def get_blocks(network, block_type="count", today=False):
    cache_file_path = os.path.join(get_current_script_directory(), f".{network}_blocks_cache.json")
    if not os.path.exists(cache_file_path):
        log_it("e", f"Cache file for network {network} does not exist.")
        return None
    try:
        with open(cache_file_path, "r") as f:
            block_data = json.load(f)

        if block_type == "count":
            return block_data['block_count']

        if block_type == "all_signed_blocks" and today:
            today_count = 0
            today_str = datetime.now().strftime("%a, %d %b %Y")
            for _, value in block_data['all_signed_blocks'].items():
                if today_str in value['ts_created']:
                    today_count += 1
            return today_count

        if block_type == "all_signed_blocks":
            blocks_per_day = {}
            for _, value in block_data['all_signed_blocks'].items():
                block_date = datetime.strptime(value['ts_created'], "%a, %d %b %Y %H:%M:%S")
                day_str = block_date.strftime("%a, %d %b %Y")
                if day_str in blocks_per_day:
                    blocks_per_day[day_str] += 1
                else:
                    blocks_per_day[day_str] = 1
            return dict(sorted(blocks_per_day, key=lambda x: datetime.strptime(x, "%a, %d %b %Y")))

        if block_type == "first_signed_blocks" and today:
            today_count = 0
            today_str = datetime.now().strftime("%a, %d %b %Y")
            for _, value in block_data['all_first_signed_blocks'].items():
                if today_str in value['ts_created']:
                    today_count += 1
            return today_count

        if block_type == "first_signed_blocks":
            first_signed_blocks_per_day = {}
            for _, value in block_data['all_first_signed_blocks'].items():
                first_signed_block_date = datetime.strptime(value['ts_created'], "%a, %d %b %Y %H:%M:%S")
                day_str = first_signed_block_date.strftime("%a, %d %b %Y")
                if day_str in first_signed_blocks_per_day:
                    first_signed_blocks_per_day[day_str] += 1
                else:
                    first_signed_blocks_per_day[day_str] = 1
            return dict(sorted(first_signed_blocks_per_day, key=lambda x: datetime.strptime(x, "%a, %d %b %Y")))

        if block_type == "all_signed_blocks_count":
            return len(block_data['all_signed_blocks'])

        if block_type == "first_signed_blocks_count":
            return len(block_data['all_first_signed_blocks'])

        if block_type == "all_signed_blocks":
            return block_data['all_signed_blocks']

        return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None