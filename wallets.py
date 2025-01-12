from logger import log_it
from common import cli_command
import re

def get_reward_wallet_tokens(wallet):
    try:
        reward_wallet =  {}
        cmd_get_wallet_info = cli_command(f"wallet info -addr {wallet}")
        if cmd_get_wallet_info:
            tokens = re.findall(r"coins:\s+([\d.]+)[\s\S]+?ticker:\s+(\w+)", cmd_get_wallet_info)
            if tokens:
                for token in tokens:
                    log_it("d", f"Found {token} token in wallet {wallet}")
                    reward_wallet[token[1]] = float(token[0])
            return reward_wallet
        else:
            return None
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        return None