from datetime import datetime
from logger import log_it
from networkutils import get_active_networks, get_network_config, get_node_data
from common import cli_command, get_current_script_directory
import re, time, json, os

CACHE_LOCK_FILE = os.path.join(get_current_script_directory(), ".cache.lock")

def is_locked():
    return os.path.exists(CACHE_LOCK_FILE)

def create_lock():
    with open(CACHE_LOCK_FILE, 'w') as lock_file:
        lock_file.write(f"Locked at {datetime.now()}\n")

def release_lock():
    if os.path.exists(CACHE_LOCK_FILE):
        os.remove(CACHE_LOCK_FILE)

def parse_tx_history(tx_history):
    rewards = []
    reward = {}
    is_receiving_reward = False
    for line in tx_history.splitlines():
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
    return rewards

def parse_blocks(data, block_type):
    parsed_blocks = {}
    block_number = None
    if data:
        log_it("d", f"Parsing {block_type.replace('_', ' ').capitalize()}...")
        lines = data.splitlines()
        for line in lines:
            line = line.strip()
            if "block number" in line:
                block_number = line.split("block number:")[1].strip()
                parsed_blocks[block_number] = {}
            elif "hash:" in line and block_number:
                parsed_blocks[block_number]['hash'] = line.split("hash:")[1].strip()
            elif "ts_create:" in line and block_number:
                original_date = line.split("ts_create:")[1].strip()[:-6]
                parsed_blocks[block_number]['ts_created'] = original_date
    return parsed_blocks

def cache_blocks_data():
    try:
        while is_locked():
            log_it("i", "Caching is already in progress, waiting for lock to release...")
            time.sleep(1)

        create_lock()

        today = datetime.now().strftime("%y%m%d")
        networks = get_active_networks()
        log_it("d", f"Found the following networks: {networks}")
        for network in networks:
            log_it("d", f"Caching blocks for {network}...")
            net_config = get_network_config(network)
            log_it("d", f"Network config for {network} returned {net_config}")
            if net_config:
                log_it("i", "Caching blocks...")
                start_time = time.time()
                block_data = {
                    'blocks_today_in_network': 0,
                    'block_count': 0,
                    'all_first_signed_blocks': {},
                    'all_signed_blocks': {}
                }

                blocks_today_in_network = cli_command(f"block list -from_date {today} -to_date {today} -net {network}", timeout=360)
                block_count = cli_command(f"block count -net {network}", timeout=360)
                first_signed_blocks = cli_command(f"block list -net {network} first_signed -cert {net_config['blocks_sign_cert']}", timeout=360)
                signed_blocks = cli_command(f"block list -net {network} signed -cert {net_config['blocks_sign_cert']}", timeout=360)

                blocks_today_in_network_match = re.search(r"have blocks: (\d+)", blocks_today_in_network)

                if blocks_today_in_network and blocks_today_in_network_match:
                    block_data['blocks_today_in_network'] = int(blocks_today_in_network_match.group(1))

                block_count_match = re.search(r":\s+(\d+)", block_count)

                if block_count and block_count_match:
                    block_data['block_count'] = int(block_count_match.group(1))

                block_data['all_first_signed_blocks'] = parse_blocks(first_signed_blocks, "first_signed_blocks")
                block_data['all_signed_blocks'] = parse_blocks(signed_blocks, "signed_blocks")

                cache_file_path = os.path.join(get_current_script_directory(), f".{network}_blocks_cache.json")
                with open(cache_file_path, "w") as f:
                    json.dump(block_data, f, indent=4)
                elapsed_time = time.time() - start_time
                log_it("i", f"Blocks cached for {network}! It took {elapsed_time:.2f} seconds!")

            else:
                log_it("e", f"Network config not found for {network}, skipping caching")
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
    finally:
        release_lock()

def cache_rewards_data():
    try:
        while is_locked():
            log_it("i", "Caching is already in progress, waiting for lock to release...")
            time.sleep(1)

        create_lock()

        networks = get_active_networks()
        log_it("d", f"Found the following networks: {networks}")

        for network in networks:
            log_it("d", f"Caching rewards for {network}...")
            net_config = get_network_config(network)
            log_it("d", f"Network config for {network} returned: {net_config}")
            node_data = get_node_data(network)
            sovereign_wallet_addr = None

            for node in node_data['nodes']:
                if node['is_my_node'] and node['is_sovereign']:
                    log_it("d", f"This node is sovereign!")
                    sovereign_wallet_addr = node['sovereign_addr']
                    log_it("d", f"Sovereign wallet address found: {sovereign_wallet_addr}")

            if net_config:  # net_config has to return something always
                log_it("i", "Caching rewards...")
                start_time = time.time()

                rewards = {}
                cmd_get_config_wallet_tx_history = cli_command(f"tx_history -addr {net_config['wallet']}", timeout=360)
                cmd_get_sovereign_wallet_tx_history = (
                    cli_command(f"tx_history -addr {sovereign_wallet_addr}", timeout=360)
                    if sovereign_wallet_addr else None
                )
                if cmd_get_config_wallet_tx_history:
                    log_it("d", f"Caching wallet history for address {net_config['wallet']}")
                    rewards['own_rewards'] = parse_tx_history(cmd_get_config_wallet_tx_history)
                if cmd_get_sovereign_wallet_tx_history:
                    log_it("d", f"Caching wallet history for address {sovereign_wallet_addr}")
                    rewards['sovereign_rewards'] = parse_tx_history(cmd_get_sovereign_wallet_tx_history)
                if rewards:
                    cache_file_path = os.path.join(get_current_script_directory(), f".{network}_rewards_cache.json")
                    with open(cache_file_path, "w") as f:
                        json.dump(rewards, f, indent=4)
                elapsed_time = time.time() - start_time
                log_it("i", f"Reward caching took {elapsed_time:.2f} seconds!")
            else:
                log_it("e", f"No valid address found for {network}, skipping caching.")
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
    finally:
        release_lock()
