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
                    'signed_blocks_count': 0,
                    'first_signed_blocks_count': 0,
                    'all_signed_blocks': {}
                }
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'block_count': executor.submit(cli_command, f"block count -net {network}"),
                        'first_signed_blocks': executor.submit(cli_command, f"block list -net {network} first_signed -cert {net_config['blocks_sign_cert']} -limit 1"),
                        'signed_blocks': executor.submit(cli_command, f"block list -net {network} signed -cert {net_config['blocks_sign_cert']}")
                    }
                block_count_result = futures['block_count'].result()
                block_count_match = re.search(r":\s+(\d+)", block_count_result)
                if block_count_match:
                    block_data['block_count'] = int(block_count_match.group(1))
                signed_blocks_result = futures["signed_blocks"].result()
                signed_blocks_match = re.search(r"have blocks: (\d+)", signed_blocks_result)
                if signed_blocks_match:
                    block_data['signed_blocks_count'] = int(signed_blocks_match.group(1))
                first_signed_match = re.search(r"have blocks: (\d+)", futures["first_signed_blocks"].result())
                if first_signed_match:
                    block_data['first_signed_blocks_count'] = int(first_signed_match.group(1))
                blocks_signed_per_day = {}
                lines = signed_blocks_result.splitlines()
                for line in lines:
                    if "ts_create:" in line:
                        timestamp_str = line.split("ts_create:")[1].strip()[:-6]
                        block_time = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S")
                        block_day = block_time.strftime("%a, %d %b %Y")
                        blocks_signed_per_day[block_day] = blocks_signed_per_day.get(block_day, 0) + 1
                sorted_blocks = dict(list(sorted(blocks_signed_per_day.items(), key=lambda x: datetime.strptime(x[0], "%a, %d %b %Y"))))
                block_data["all_signed_blocks"] = sorted_blocks
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
                cmd_get_tx_history = cli_command(f"tx_history -addr {net_config['wallet']}")
                rewards = []
                reward = {}
                is_receiving_reward = False
                if cmd_get_tx_history:
                    lines = cmd_get_tx_history.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith("status: ACCEPTED"):
                            if reward and is_receiving_reward:
                                rewards.append(reward)
                            reward = {}
                            is_receiving_reward = False
                            continue
                        if line.startswith("hash:"):
                            reward['hash'] = line.split("hash:")[1].strip()
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