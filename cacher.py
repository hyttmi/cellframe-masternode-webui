from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logger import log_it
from networkutils import get_active_networks, get_network_config
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
                lines = first_signed_blocks_result.splitlines()
                all_first_signed_blocks = []
                first_signed_block = {}
                is_new_first_signed_block = False
                for line in lines:
                    line = line.strip()
                    if "block number" in line: # we don't need this in the cache
                        if first_signed_block and is_new_first_signed_block:
                            all_first_signed_blocks.append(block)
                        first_signed_block = {}
                        is_new_first_signed_block = False
                        continue
                    if "hash:" in line:
                        block['hash'] = line.split("hash:")[1].strip()
                        continue
                    if "ts_create:" in line:
                        original_date = line.split("ts_create:")[1].strip()[:-6]
                        block['ts_created'] = original_date
                        is_new_first_signed_block = True
                        continue
                if first_signed_block and is_new_first_signed_block:
                    all_first_signed_blocks.append(first_signed_block)
                block_data['all_first_signed_blocks'] = all_blocks

                signed_blocks_result = futures["signed_blocks"].result()
                lines = signed_blocks_result.splitlines()
                all_blocks = []
                block = {}
                is_new_block = False
                for line in lines:
                    line = line.strip()
                    if "block number" in line: # we don't need this in the cache
                        if block and is_new_block:
                            all_blocks.append(block)
                        block = {}
                        is_new_block = False
                        continue
                    if "hash:" in line:
                        block['hash'] = line.split("hash:")[1].strip()
                        continue
                    if "ts_create:" in line:
                        original_date = line.split("ts_create:")[1].strip()[:-6]
                        block['ts_created'] = original_date
                        is_new_block = True
                        continue
                if block and is_new_block:
                    all_blocks.append(block)
                block_data["all_signed_blocks"] = all_blocks
                cache_file_path = os.path.join(get_current_script_directory(), f".{network}_blocks_cache.json")
                with open(cache_file_path, "w") as f:
                    json.dump(block_data, f, indent=4)
                elapsed_time = time.time() - start_time
                log_it("i",f"Blocks cached for {network}! It took {elapsed_time:.2f} seconds!")
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
            if net_config:
                log_it("i", "Caching rewards...")
                start_time = time.time()
                cmd_get_tx_history = cli_command(f"tx_history -addr {net_config['wallet']}", timeout=360) # Increase timeout to 6 minutes
                rewards = []
                reward = {}
                is_receiving_reward = False
                if cmd_get_tx_history:
                    lines = cmd_get_tx_history.splitlines()
                    for line in lines:
                        line = line.strip()
                        if "status: ACCEPTED" in line:
                            if reward and is_receiving_reward:
                                rewards.append(reward)
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
                        rewards.append(reward)
                    cache_file_path = os.path.join(get_current_script_directory(), f".{network}_rewards_cache.json")
                    with open(cache_file_path, "w") as f:
                        json.dump(rewards, f, indent=4)
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    log_it("i", f"Rewards cached for {network}! It took {elapsed_time:.2f} seconds!")
                else:
                    log_it("e", f"Failed to fetch transaction history!")
            else:
                log_it("e", f"Network config not found for {network}, skipping caching.")
                return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None