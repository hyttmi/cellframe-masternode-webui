from datetime import datetime
from logger import log_it
from networkutils import get_active_networks, get_network_config, get_node_data, is_node_synced
import re, time, json, os, traceback
from notifications import notify_all
from utils import Utils

CACHE_LOCK_FILE = os.path.join(Utils.get_current_script_directory(), ".cache.lock")

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
    parsed_blocks = []
    block_info = None
    if not data:
        log_it("d", f"No data to parse from {block_type.replace('_', ' ').capitalize()}")
        return parsed_blocks
    log_it("d", f"Parsing {block_type.replace('_', ' ').capitalize()}...")
    for line in data.splitlines():
        line = line.strip()
        if line.startswith("block number:"):
            if block_info:
                parsed_blocks.append(block_info)
            block_info = {"block_number": line.split("block number:")[1].strip()}
        elif line.startswith("hash:") and block_info:
            block_info["hash"] = line.split("hash:")[1].strip()
        elif line.startswith("ts_create:") and block_info:
            block_info["ts_created"] = line.split("ts_create:")[1].strip()[:-6]
    if block_info:
        parsed_blocks.append(block_info)
    return parsed_blocks

def cache_blocks_data():
    try:
        while is_locked():
            log_it("i", "Caching is already in progress, waiting for lock to release...")
            Utils.delay(30)

        create_lock()
        today = datetime.now().strftime("%y%m%d")
        networks = get_active_networks()
        log_it("d", f"Found the following networks: {networks}")
        for network in networks:
            log_it("d", f"Caching blocks for {network}...")
            net_config = get_network_config(network)
            if net_config:
                while not is_node_synced(network) or not Utils.is_cli_ready():
                    log_it("i", "Network seems not to be synced or cli is not responding, sleeping for 10 seconds...")
                    Utils.delay(10)
                log_it("i", f"Caching blocks for {network}...")
                notify_all(f"Caching blocks for {network}...", channels=["websocket"])
                start_time = time.time()
                block_data = {
                    'last_run': None,
                    'blocks_today_in_network': 0,
                    'block_count': 0,
                    'all_first_signed_blocks': {},
                    'all_signed_blocks': {}
                }

                blocks_today_in_network = Utils.cli_command(f"block list -from_date {today} -to_date {today} -net {network}", timeout=360)
                block_count = Utils.cli_command(f"block count -net {network}", timeout=360)
                first_signed_blocks = Utils.cli_command(f"block list -net {network} first_signed -cert {net_config['blocks_sign_cert']}", timeout=360)
                signed_blocks = Utils.cli_command(f"block list -net {network} signed -cert {net_config['blocks_sign_cert']}", timeout=360)

                blocks_today_in_network_match = re.search(r"have blocks: (\d+)", blocks_today_in_network)

                if blocks_today_in_network and blocks_today_in_network_match:
                    block_data['blocks_today_in_network'] = int(blocks_today_in_network_match.group(1))

                block_count_match = re.search(r":\s+(\d+)", block_count)

                if block_count and block_count_match:
                    block_data['block_count'] = int(block_count_match.group(1))

                if first_signed_blocks:
                    block_data['all_first_signed_blocks'] = parse_blocks(first_signed_blocks, "first_signed_blocks")

                if signed_blocks:
                    block_data['all_signed_blocks'] = parse_blocks(signed_blocks, "signed_blocks")
                    block_data['last_run'] = datetime.now().isoformat()

                cache_file_path = os.path.join(Utils.get_current_script_directory(), f".{network}_blocks_cache.json")
                with open(cache_file_path, "w") as f:
                    json.dump(block_data, f, indent=4)
                elapsed_time = time.time() - start_time
                log_it("i", f"Blocks cached for {network}! It took {elapsed_time:.2f} seconds!")
                notify_all(f"Blocks cached for {network}! It took {elapsed_time:.2f} seconds!", channels=["websocket"])
            else:
                log_it("i", f"Network config not found for {network}, skipping caching")
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
    finally:
        release_lock()

def cache_rewards_data():
    try:
        while is_locked():
            log_it("i", "Caching is already in progress, waiting for lock to release...")
            Utils.delay(30)

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
                while not is_node_synced(network) or not Utils.is_cli_ready():
                    log_it("i", "Network seems not to be synced or cli is not responding, sleeping for 10 seconds...")
                    Utils.delay(10)
                log_it("i", f"Caching rewards for {network}...")
                notify_all(f"Caching rewards for {network}...", channels=["websocket"])
                start_time = time.time()

                rewards = {}
                cmd_get_config_wallet_tx_history = Utils.cli_command(f"tx_history -addr {net_config['wallet']}", timeout=360)
                cmd_get_sovereign_wallet_tx_history = (
                    Utils.cli_command(f"tx_history -addr {sovereign_wallet_addr}", timeout=360)
                    if sovereign_wallet_addr else None
                )
                if cmd_get_config_wallet_tx_history:
                    log_it("d", f"Caching wallet history for address {net_config['wallet']}")
                    rewards['own_rewards'] = parse_tx_history(cmd_get_config_wallet_tx_history)
                if cmd_get_sovereign_wallet_tx_history:
                    log_it("d", f"Caching wallet history for address {sovereign_wallet_addr}")
                    rewards['sovereign_rewards'] = parse_tx_history(cmd_get_sovereign_wallet_tx_history)
                if rewards:
                    rewards['last_run'] = datetime.now().isoformat()
                    cache_file_path = os.path.join(Utils.get_current_script_directory(), f".{network}_rewards_cache.json")
                    with open(cache_file_path, "w") as f:
                        json.dump(rewards, f, indent=4)
                elapsed_time = time.time() - start_time
                log_it("i", f"Reward caching for {network} took {elapsed_time:.2f} seconds!")
                notify_all(f"Reward caching for {network} took {elapsed_time:.2f} seconds!", channels=["websocket"])
            else:
                log_it("i", f"No valid address found for {network}, skipping caching.")
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
    finally:
        release_lock()
