try:
    from logger import log_it
    from common import cli_command
    import re, inspect
except ImportError as e:
    log_it("e", f"ImportError: {e}")

def get_reward_wallet_tokens(wallet):
    try:
        cmd_get_wallet_info = cli_command(f"wallet info -addr {wallet}")
        if cmd_get_wallet_info:
            tokens = re.findall(r"coins:\s+([\d.]+)[\s\S]+?ticker:\s+(\w+)", cmd_get_wallet_info)
            return tokens
        else:
            return None
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        return None