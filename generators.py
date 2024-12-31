from utils import (
    format_uptime,
    get_installed_node_version,
    get_latest_node_version,
    get_sys_stats,
    get_system_hostname,
    get_external_ip
)
from networkutils import (
    get_active_networks,
    get_autocollect_status,
    get_blocks,
    get_network_config,
    get_network_status,
    get_node_data,
    get_node_dump,
    get_rewards,
    get_token_price,
    get_current_block_reward
)
from updater import check_plugin_update
from wallets import get_reward_wallet_tokens
from logger import log_it
from common import get_current_script_directory
from config import Config
from concurrent.futures import ThreadPoolExecutor
import inspect, json, os
        
def generate_general_info(format_time=True):
    try:
        sys_stats = get_sys_stats()
        plugin_data = check_plugin_update()
        info = {
                'current_plugin_version': plugin_data['current_version'],
                'latest_plugin_version': plugin_data['latest_version'],
                'plugin_name': Config.PLUGIN_NAME,
                'hostname': get_system_hostname(),
                'system_uptime': format_uptime(sys_stats['system_uptime']) if format_time else sys_stats['system_uptime'],
                'node_uptime': format_uptime(sys_stats['node_uptime']) if format_time else sys_stats['node_uptime'],
                'node_version': get_installed_node_version(),
                'latest_node_version': get_latest_node_version(),
                'node_cpu_usage': sys_stats['node_cpu_usage'],
                'node_memory_usage': sys_stats['node_memory_usage_mb'],
                'external_ip': get_external_ip()
        }
        log_it("d", json.dumps(info, indent=4))
        return info
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None

def generate_network_info():
    try:
        network_data = {}
        networks = get_active_networks()
        log_it("d", f"Found the following networks: {networks}")
        for network in networks:
            net_config = get_network_config(network)
            if net_config:
                network = str(network)
                log_it("d", f"Fetching data for {network} network...")
                wallet = net_config['wallet']
                tokens = get_reward_wallet_tokens(wallet)
                net_status = get_network_status(network)
                with ThreadPoolExecutor() as executor:
                    futures = {
                        'all_blocks': executor.submit(get_blocks, network, block_type="count"),
                        'all_signed_blocks_dict': executor.submit(get_blocks, network, block_type="all_signed_blocks"),
                        'all_signed_blocks': executor.submit(get_blocks, network, block_type="all_signed_blocks_count"),
                        'autocollect_status': executor.submit(get_autocollect_status, network),
                        'current_block_reward': executor.submit(get_current_block_reward, network),
                        'first_signed_blocks': executor.submit(get_blocks, network, block_type="first_signed_blocks_count"),
                        'general_node_info': executor.submit(get_node_dump, network),
                        'node_data': executor.submit(get_node_data, network),
                        'rewards': executor.submit(get_rewards, network, total_sum=False),
                        'rewards_today': executor.submit(get_rewards, network, rewards_today=True),
                        'signed_blocks_today': executor.submit(get_blocks, network, block_type="all_signed_blocks", today=True),
                        'sum_rewards': executor.submit(get_rewards, network, total_sum=True),
                        'token_price': executor.submit(get_token_price, network)
                    }
                    network_info = {
                        'address': net_status['address'],
                        'all_blocks': futures['all_blocks'].result(),
                        'all_rewards': futures['sum_rewards'].result(),
                        'all_signed_blocks_dict': futures['all_signed_blocks_dict'].result(),
                        'all_signed_blocks': futures['all_signed_blocks'].result(),
                        'autocollect_rewards': futures['autocollect_status'].result()['rewards'],
                        'autocollect_status': futures['autocollect_status'].result()['active'],
                        'current_block_reward': futures['current_block_reward'].result(),
                        'fee_wallet_tokens': {token[1]: float(token[0]) for token in tokens} if tokens else None,
                        'first_signed_blocks': futures['first_signed_blocks'].result(),
                        'general_node_info': futures['general_node_info'].result(),
                        'node_data': futures['node_data'].result(),
                        'rewards': futures['rewards'].result(),
                        'rewards_today': futures['rewards_today'].result(),
                        'signed_blocks_today': futures['signed_blocks_today'].result(),
                        'state': net_status['state'],
                        'target_state': net_status['target_state'],
                        'token_price': futures['token_price'].result()
                    }
                    network_data[network] = network_info
        log_it("d", json.dumps(network_data, indent=4))
        return network_data if network_data else None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None
    
def generate_data(template_name, return_as_json=False, is_top_level_template=False):
    try:
        if return_as_json:
            general_info = generate_general_info(format_time=False)
            network_info = generate_network_info()
            response = json.dumps({"general_info": general_info, "network_info": network_info}, indent=4)
            log_it("d", response)
            return response
        general_info = generate_general_info(format_time=True)
        network_info = generate_network_info()
        if general_info:
            custom_template_path = os.path.join(
                get_current_script_directory(), "templates", "custom_templates"
            )
            template_path = template_name if is_top_level_template else f"{Config.TEMPLATE}/{template_name}"
            if os.path.exists(custom_template_path) and is_top_level_template:
                custom_template_file = os.path.join(custom_template_path, template_name)
                if os.path.isfile(custom_template_file):
                    template_path = custom_template_file
            log_it("d", "Generating HTML content...")
            env = Config.jinja_environment()
            template = env.get_template(template_path)
            return template.render(general_info=general_info, network_info=network_info)
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        if return_as_json:
            return json.dumps({"error": f"Error generating data: {e}"}).encode("utf-8")
        else:
            return f"<h1>Error: {e}</h1>"