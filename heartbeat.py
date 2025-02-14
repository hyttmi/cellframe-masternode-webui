from networkutils import (
    get_active_networks,
    get_network_config,
    get_autocollect_status,
    get_blocks
)
from logger import log_it
from datetime import datetime, timedelta

class Heartbeat:
    def __init__(self):
        self.statuses = {
            network: {
                "autocollect_status": "Unknown",
                "signed_blocks": "Unknown"
            }
            for network in get_active_networks() if get_network_config(network)
        }
        log_it("d", self.statuses)

    def autocollect_status(self):
        try:
            for network in self.statuses:
                autocollect_status = get_autocollect_status(network)
                if autocollect_status['active'] == "Active":
                    self.statuses[network]["autocollect_status"] = "OK"
                else:
                    self.statuses[network]["autocollect_status"] = "NOK"
                    log_it("e", f"[HEARTBEAT] Autocollect status seems to be inactive!")
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

    def last_signed_block(self):
        try:
            for network in self.statuses:
                signed_blocks = get_blocks(network, block_type="all_signed_blocks", heartbeat=True)
                log_it("d", signed_blocks)
                curr_time = datetime.now()
                for block in signed_blocks.items():
                    log_it("d", block)
                    block_time = datetime.strptime(block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                    if curr_time - block_time > timedelta(hours=12):
                        self.statuses[network]['signed_blocks'] = "NOK"
                        log_it("e", f"[HEARTBEAT] Signed block {block['tx_hash']} is older than 12 hours!")
                        break
                else:
                    self.statuses[network]['signed_blocks'] = "OK"
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

def run_heartbeat_check():
    heartbeat = Heartbeat()
    heartbeat.autocollect_status()
    heartbeat.last_signed_block()
    log_it("d", f"Updated heartbeat statuses: {heartbeat.statuses}")