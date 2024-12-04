try:
    from utils import (
        check_plugin_update,
        format_uptime,
        get_installed_node_version,
        get_latest_node_version,
        get_sys_stats,
        get_system_hostname
    )
    
    from networkutils import (
        get_active_networks,
        get_autocollect_rewards,
        get_autocollect_status,
        get_blocks,
        get_current_stake_value,
        get_network_config,
        get_network_status,
        get_node_dump,
        get_reward_wallet_tokens,
        get_token_price,
        get_rewards,
    )
    
    from logger import log_it
    from config import Config
    from concurrent.futures import ThreadPoolExecutor
    
except ImportError as e:
    log_it("e", f"ImportError: {e}")
        
def generate_general_info(format_time=True):
    try:
        sys_stats = get_sys_stats()
        is_update_available, curr_version, latest_version = check_plugin_update()
        info = {
                'plugin_update_available': is_update_available,
                'current_plugin_version': curr_version,
                'latest_plugin_version': latest_version,
                'plugin_name': Config.PLUGIN_NAME,
                'hostname': get_system_hostname(),
                'system_uptime': format_uptime(sys_stats['system_uptime']) if format_time else sys_stats['system_uptime'],
                'node_uptime': format_uptime(sys_stats['node_uptime']) if format_time else sys_stats['node_uptime'],
                'node_version': get_installed_node_version(),
                'latest_node_version': get_latest_node_version(),
                'node_cpu_usage': sys_stats['node_cpu_usage'],
                'node_memory_usage': sys_stats['node_memory_usage_mb']
                
        }
        return info
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None

def generate_network_info():
    try:
        network_data = {}
        networks = get_active_networks()
        log_it("i", f"Found the following networks: {networks}")
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
                        'first_signed_blocks': executor.submit(get_blocks, network, block_type="first_signed_blocks_count"),
                        'all_signed_blocks_dict': executor.submit(get_blocks, network, block_type="all_signed_blocks"),
                        'all_signed_blocks': executor.submit(get_blocks, network, block_type="all_signed_blocks_count"),
                        'all_blocks': executor.submit(get_blocks, network, block_type="count"),
                        'signed_blocks_today': executor.submit(get_blocks, network, block_type="all_signed_blocks", today=True),
                        'token_price': executor.submit(get_token_price, network),
                        'rewards': executor.submit(get_rewards, network, total_sum=False),
                        'sum_rewards': executor.submit(get_rewards, network, total_sum=True),
                        'node_stake_value': executor.submit(get_current_stake_value, network),
                        'general_node_info': executor.submit(get_node_dump, network),
                        'autocollect_status': executor.submit(get_autocollect_status, network),
                        'autocollect_rewards': executor.submit(get_autocollect_rewards, network)
                    }
                    network_info = {
                        'state': net_status['state'],
                        'target_state': net_status['target_state'],
                        'address': net_status['address'],
                        'first_signed_blocks': futures['first_signed_blocks'].result(),
                        'all_signed_blocks_dict': futures['all_signed_blocks_dict'].result(),
                        'all_signed_blocks': futures['all_signed_blocks'].result(),
                        'all_blocks': futures['all_blocks'].result(),
                        'signed_blocks_today': futures['signed_blocks_today'].result(),
                        'autocollect_status': futures['autocollect_status'].result(),
                        'autocollect_rewards': futures['autocollect_rewards'].result(),
                        'fee_wallet_tokens': {token[1]: float(token[0]) for token in tokens} if tokens else None,
                        'rewards': futures['rewards'].result(),
                        'all_rewards': futures['sum_rewards'].result(),
                        'token_price': futures['token_price'].result(),
                        'node_stake_value': futures['node_stake_value'].result(),
                        'general_node_info': futures['general_node_info'].result()
                    }
                    network_data[network] = network_info
                log_it("i", network_data)
                return network_data
        else:
            return None
    except Exception as e:
        log_it("e", f"Error: {e}")
        return None
    
def generate_html(template_name):
    try:
        general_info = generate_general_info(format_time=True)
        network_info = generate_network_info()
        if generate_general_info:
            template = Config.TEMPLATE
            template_path = f"{template}/{template_name}"
            log_it("i", "Generating HTML content...")
            env = Config.jinja_environment()
            template = env.get_template(template_path)
            return template.render(general_info=general_info, network_info=network_info)
    except Exception as e:
        log_it("e", f"Error: {e}")
