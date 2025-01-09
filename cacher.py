from concurrent.futures import ThreadPoolExecutor
from logger import log_it
from networkutils import get_active_networks, get_network_config, get_node_data
from common import cli_command, get_current_script_directory
import re, time, json, os, inspect

def cache_blocks_data():
    try:
        networks = get_active_networks()
        log_it("d", f"Found the following networks: {networks}")
        for network in networks:
            net_config = get_network_config(network)
            if net_config:
                log_it("i", "Caching blocks...")
                start_time = time.time()
                block_data = {
                    'block_count': 0,
                    'all_first_signed_blocks': {},
                    'all_signed_blocks': {}
                }
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'block_count': executor.submit(cli_command, f"block count -net {network}"),
                        'first_signed_blocks': executor.submit(cli_command, f"block list -net {network} first_signed -cert {net_config['blocks_sign_cert']}"),
                        'signed_blocks': executor.submit(cli_command, f"block list -net {network} signed -cert {net_config['blocks_sign_cert']}")
                    }

                block_count_result = futures['block_count'].result()
                block_count_match = re.search(r":\s+(\d+)", block_count_result)

                if block_count_result and block_count_match:
                    block_data['block_count'] = int(block_count_match.group(1))

                first_signed_blocks_result = futures['first_signed_blocks'].result()
                if first_signed_blocks_result:
                    lines = first_signed_blocks_result.splitlines()
                    for line in lines:
                        line = line.strip()
                        if "block number" in line:
                            block_number = line.split("block number:")[1].strip()
                            block_data['all_first_signed_blocks'][block_number] = {}
                        elif "hash:" in line:
                            block_data['all_first_signed_blocks'][block_number]['hash'] = line.split("hash:")[1].strip()
                        elif "ts_create:" in line:
                            original_date = line.split("ts_create:")[1].strip()[:-6]
                            block_data['all_first_signed_blocks'][block_number]['ts_created'] = original_date

                signed_blocks_result = futures["signed_blocks"].result()
                if signed_blocks_result:
                    lines = signed_blocks_result.splitlines()
                    for line in lines:
                        line = line.strip()
                        if "block number" in line:
                            block_number = line.split("block number:")[1].strip()
                            block_data['all_signed_blocks'][block_number] = {}
                        elif "hash:" in line:
                            block_data['all_signed_blocks'][block_number]['hash'] = line.split("hash:")[1].strip()
                        elif "ts_create:" in line:
                            original_date = line.split("ts_create:")[1].strip()[:-6]
                            block_data['all_signed_blocks'][block_number]['ts_created'] = original_date

                cache_file_path = os.path.join(get_current_script_directory(), f".{network}_blocks_cache.json")
                with open(cache_file_path, "w") as f:
                    json.dump(block_data, f, indent=4)
                elapsed_time = time.time() - start_time
                log_it("i", f"Blocks cached for {network}! It took {elapsed_time:.2f} seconds!")
            else:
                log_it("e", f"Network config not found for {network}, skipping caching")
                return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def cache_rewards_data():
    try:
        networks = get_active_networks()
        log_it("d", f"Found the following networks: {networks}")
        for network in networks:
            net_config = get_network_config(network)
            node_data = get_node_data(network)
            sovereign_wallet_addr = None
            for node in node_data['nodes']:
                if node['is_my_node'] and node['is_sovereign']:
                    sovereign_wallet_addr = node['sovereign_addr']
                    log_it("d", f"Sovereign wallet address found: {sovereign_wallet_addr}")
            if net_config: # net_config has to return something always
                log_it("i", "Caching rewards...")
                start_time = time.time()

                with ThreadPoolExecutor() as executor:
                    futures = {
                        'cmd_get_config_wallet_tx_history': executor.submit(cli_command, f"tx_history -addr {net_config['wallet']}", timeout=360),
                    }

                    if sovereign_wallet_addr:
                        futures['cmd_get_sovereign_wallet_tx_history'] = executor.submit(cli_command, f"tx_history -addr {sovereign_wallet_addr}", timeout=360)

                rewards = {}

                own_wallet_history = futures['cmd_get_config_wallet_tx_history'].result()
                if own_wallet_history:
                    rewards['own_rewards'] = []
                    log_it("d", f"Caching wallet history for address {net_config['wallet']}")
                    reward = {}
                    is_receiving_reward = False
                    lines = own_wallet_history.splitlines()
                    for line in lines:
                        line = line.strip()
                        if "status: ACCEPTED" in line:
                            if reward and is_receiving_reward:
                                rewards['own_rewards'].append(reward)
                            reward = {}
                            is_receiving_reward = False
                            continue
                        if "hash:" in line:
                            reward['hash'] = line.split("hash:")[1].strip()
                            continue
                        if "tx_created:" in line:
                            original_date = line.split("tx_created:")[1].strip()[:-6]
                            reward['tx_created'] = original_date
                            continue
                        if "recv_coins:" in line:
                            reward['recv_coins'] = line.split("recv_coins:")[1].strip()
                            continue
                        if "source_address: reward collecting" in line:
                            is_receiving_reward = True
                            continue
                    if reward and is_receiving_reward:
                        rewards['own_rewards'].append(reward)

                if 'cmd_get_sovereign_wallet_tx_history' in futures:
                    sovereign_wallet_history = futures['cmd_get_sovereign_wallet_tx_history'].result()
                    if sovereign_wallet_history:
                        rewards['sovereign_rewards'] = []
                        log_it("d", f"Caching wallet history for address {sovereign_wallet_addr}")
                        reward = {}
                        is_receiving_reward = False
                        lines = sovereign_wallet_history.splitlines()
                        for line in lines:
                            line = line.strip()
                            if "status: ACCEPTED" in line:
                                if reward and is_receiving_reward:
                                    rewards['sovereign_rewards'].append(reward)
                                reward = {}
                                is_receiving_reward = False
                                continue
                            if "hash:" in line:
                                reward['hash'] = line.split("hash:")[1].strip()
                                continue
                            if "tx_created:" in line:
                                original_date = line.split("tx_created:")[1].strip()[:-6]
                                reward['tx_created'] = original_date
                                continue
                            if "recv_coins:" in line:
                                reward['recv_coins'] = line.split("recv_coins:")[1].strip()
                                continue
                            if "source_address: reward collecting" in line:
                                is_receiving_reward = True
                                continue
                        if reward and is_receiving_reward:
                            rewards['sovereign_rewards'].append(reward)
                if rewards:
                    cache_file_path = os.path.join(get_current_script_directory(), f".{network}_rewards_cache.json")
                    with open(cache_file_path, "w") as f:
                        json.dump(rewards, f, indent=4)
                end_time = time.time()
                elapsed_time = end_time - start_time
                log_it("i", f"Reward caching took {elapsed_time:.2f} seconds!")
            else:
                log_it("e", f"No valid address found for {network}, skipping caching.")
                return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None
