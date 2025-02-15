from common import cli_command, get_current_script_directory
from wallets import get_reward_wallet_tokens
from datetime import datetime
from logger import log_it
from pycfhelpers.node.net import CFNet
import re, requests, os, json, functools

def get_active_networks():
    try:
        nets = CFNet.active_nets()
        if nets:
            return [str(net.name) for net in nets]
        log_it("e", "Can't get list of networks!")
        return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

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
                    log_it("d", f"Found correct network config for {network}")
                    return net_config
            log_it("e", f"Necessary information missing in {network_config_file}, not a masternode?")
            return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

def get_autocollect_status(network):
    try:
        autocollect_status = {}
        autocollect_cmd = cli_command(f"block autocollect status -net {network}", timeout=3)
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
        log_it("e", "An error occurred", exc=e)
        return None

functools.lru_cache(maxsize=1)
def get_current_block_reward(network):
    try:
        block_reward_cmd = cli_command(f"block reward show -net {network}", timeout=3)
        if block_reward_cmd:
            block_reward_match = re.search(r"(\d+.\d+)", block_reward_cmd)
            if block_reward_match:
                return float(block_reward_match.group(1))
            return None
        return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

def get_token_price(network):
    try:
        log_it("d", "Fetching token price...")
        network_urls = {
            "backbone": "https://coinmarketcap.com/currencies/cellframe/",
            "kelvpn": "https://kelvpn.com/about-token"
        }
        url = network_urls.get(network.lower())
        if not url:
            log_it("e", f"Unsupported network {network}")
            return None
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            regex_patterns = {
                "backbone": r"price today is \$(\d+\.\d+)",
                "kelvpn": r"\$(\d+\.\d+)"
            }
            regex_match = re.search(regex_patterns[network.lower()], response.text)
            if regex_match:
                return float(regex_match.group(1))
            log_it("e", f"Price not found in {url}")
            return None
        log_it("e", f"Failed to fetch token price from {url}. Status code was {response.status_code}")
        return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

def get_node_data(network):
    try:
        status = get_network_status(network)
        if status:
            addr = status['address']
            list_keys = cli_command(f"srv_stake list keys -net {network}", timeout=3)
            if not list_keys:
                log_it("e", f"Failed to run srv_stake list keys for {network}")
                return None
            total_weight_in_network = re.search(r"total_weight_coins:\s+(\d+\.\d+)", list_keys)
            active_nodes_count = len(re.findall(r"active: true", list_keys))
            max_related_weight = re.search(r"each_validator_max_related_weight:\s+(\d+\.\d+)", list_keys)

            total_weight = float(total_weight_in_network.group(1))
            max_weight = float(max_related_weight.group(1))
            calculated_weight = float(total_weight * (max_weight / 100))

            node_pattern = re.compile(
                r'pkey_hash:\s+(?P<pkey_hash>\w+)\s+'
                r'stake_value:\s+(?P<stake_value>\d+\.\d+)\s+'
                r'effective_value:\s+(?P<effective_value>\d+\.\d+)\s+'
                r'related_weight:\s+(?P<related_weight>\d+\.\d+)\s+'
                r'tx_hash:\s+(?P<tx_hash>\w+)\s+'
                r'node_addr:\s+(?P<node_addr>[A-Z0-9]+::[A-Z0-9]+::[A-Z0-9]+::[A-Z0-9]+)\s+'
                r'sovereign_addr:\s+(?P<sovereign_addr>\w+)\s+'
                r'sovereign_tax:\s+(?P<sovereign_tax>\d+\.\d+)\s+'
                r'active:\s+(?P<active>true|false)'
            )
            nodes = []
            for match in node_pattern.finditer(list_keys):
                node = match.groupdict()
                node['is_my_node'] = (node['node_addr'] == addr)
                node['is_sovereign'] = float(node['sovereign_tax']) > 0.0
                nodes.append(node)

                if node['is_sovereign'] and node['is_my_node']:
                    sovereign_wallet_info = get_reward_wallet_tokens(node['sovereign_addr'])
                    if sovereign_wallet_info:
                        node['sovereign_wallet_tokens'] = sovereign_wallet_info
                    else:
                        node['sovereign_wallet_tokens'] = None
                else:
                    node['sovereign_wallet_tokens'] = None

            info = {
                'active_nodes_count': active_nodes_count,
                'total_weight': total_weight,
                'max_weight': calculated_weight
            }
            result = {
                'info': info,
                'nodes': nodes
            }
            return result
        return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

def get_network_status(network):
    try:
        net_status = cli_command(f"net -net {network} get status", timeout=3)
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
        log_it("e", "An error occurred", exc=e)
        return None

def get_rewards(network, total_sum=False, rewards_today=False, is_sovereign=False):
    try:
        rewards = {}
        cache_file_path = os.path.join(get_current_script_directory(), f".{network}_rewards_cache.json")
        with open(cache_file_path) as f:
            data = json.load(f)
            rewards_data = data.get('sovereign_rewards' if is_sovereign else 'own_rewards', None)
            if not rewards_data:
                log_it("e", f"No rewards data found for {'sovereign' if is_sovereign else 'own'} rewards in network {network}!")
                return None
            for reward in rewards_data:
                date_string = reward['tx_created']
                amount = float(reward['recv_coins'])
                formatted_date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S")
                formatted_date_str = formatted_date.strftime("%a, %d %b %Y")
                if formatted_date_str in rewards:
                    rewards[formatted_date_str] += amount
                else:
                    rewards[formatted_date_str] = amount
            sorted_dict = sorted(rewards.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y"))
            if sorted_dict:
                sorted_dict.pop()
            if total_sum:
                return sum(rewards.values())
            elif rewards_today:
                today_str = datetime.now().strftime("%a, %d %b %Y")
                return rewards.get(today_str, None)
            else:
                return dict(sorted_dict)
    except FileNotFoundError:
        log_it("e", "Rewards file not found!")
        return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

def get_blocks(network, block_type="count", today=False, heartbeat=False):
    try:
        cache_file_path = os.path.join(get_current_script_directory(), f".{network}_blocks_cache.json")
        with open(cache_file_path, "r") as f:
            block_data = json.load(f)
            all_signed_blocks = block_data.get('all_signed_blocks', [])
            all_first_signed_blocks = block_data.get('all_first_signed_blocks', [])
            block_count = block_data.get('block_count')
            blocks_today_in_network = block_data.get('blocks_today_in_network')

        if block_type == "all_signed_blocks" and heartbeat:
            return all_signed_blocks[0] if all_signed_blocks else None

        if block_type == "blocks_today_in_network":
            return blocks_today_in_network if blocks_today_in_network else None

        if block_type == "count":
            return block_count if block_count else None

        today_str = datetime.now().strftime("%a, %d %b %Y")

        if block_type == "all_signed_blocks" and today:
            return sum(1 for block in all_signed_blocks if today_str in block["ts_created"])

        if block_type == "all_signed_blocks":
            blocks_per_day = {}
            for block in all_signed_blocks:
                block_date = datetime.strptime(block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                day_str = block_date.strftime("%a, %d %b %Y")
                blocks_per_day[day_str] = blocks_per_day.get(day_str, 0) + 1

            sorted_blocks = sorted(blocks_per_day.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y"))
            if sorted_blocks:
                sorted_blocks.pop()
            return dict(sorted_blocks)

        if block_type == "first_signed_blocks" and today:
            return sum(1 for block in all_first_signed_blocks if today_str in block["ts_created"])

        if block_type == "first_signed_blocks":
            first_signed_blocks_per_day = {}
            for block in all_first_signed_blocks:
                block_date = datetime.strptime(block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                day_str = block_date.strftime("%a, %d %b %Y")
                first_signed_blocks_per_day[day_str] = first_signed_blocks_per_day.get(day_str, 0) + 1

            sorted_blocks = sorted(first_signed_blocks_per_day.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y"))
            if sorted_blocks:
                sorted_blocks.pop()
            return dict(sorted_blocks)

        if block_type == "all_signed_blocks_count":
            return len(all_signed_blocks) if all_signed_blocks else None

        if block_type == "first_signed_blocks_count":
            return len(all_first_signed_blocks) if all_first_signed_blocks else None

    except FileNotFoundError:
        log_it("e", "Blocks cache file not found!")
        return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None

def get_chain_size(network):
    try:
        network_mapping = {
            'Backbone': 'scorpion',
            'KelVPN': 'kelvpn'
        }
        if network not in network_mapping:
            log_it("d" f"Unknown network: {network}. Can't fetch chain size...")
            return None
        dir = network_mapping[network]
        chain_path = f"/opt/cellframe-node/var/lib/network/{dir}/main/0.dchaincell"
        log_it("d", f"Checking chain size for {chain_path}...")
        if not os.path.exists(chain_path):
            log_it("e", f"Chaincell file not found for {network}")
            return None
        log_it("d", f"Chain path for {network} exists!")
        size = os.path.getsize(chain_path)
        if size < 1024:
            return f"{size} bytes"
        elif size < pow(1024,2):
            return f"{round(size/1024, 2)} KB"
        elif size < pow(1024,3):
            return f"{round(size/(pow(1024,2)), 2)} MB"
        elif size < pow(1024,4):
            return f"{round(size/(pow(1024,3)), 2)} GB"
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None