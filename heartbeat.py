from networkutils import (
    get_active_networks,
    get_network_config,
    get_autocollect_status,
    get_blocks,
    change_net_mode,
    is_node_in_node_list
)
from utils import restart_node, remove_spacing
from cacher import is_locked
from config import Config
from logger import log_it
from notifications import notify_all
from datetime import datetime, timedelta
import time, traceback

class Heartbeat:
    def __init__(self):
        log_it("d", "[HEARTBEAT] Initializing heartbeat...")
        self.max_msgs_sent = Config.HEARTBEAT_NOTIFICATION_AMOUNT
        self.msgs_sent = 0
        self.in_node_list_msgs_sent = 0
        self.statuses = {
            network: {
                "autocollect_status": "Unknown",
                "last_signed_block": "Unknown",
                "in_node_list": "Unknown"
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
                    notify_all(f"({Config.NODE_ALIAS}): Autocollect status seems to be inactive!")
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    def in_node_list(self):
        try:
            for network in self.statuses:
                in_node_list = is_node_in_node_list(network)
                if in_node_list:
                    log_it("d", f"[HEARTBEAT] Node is in the node list for {network}")
                    self.statuses[network]["in_node_list"] = "OK"
                    self.in_node_list_msgs_sent = 0
                    return
                else:
                    if self.in_node_list_msgs_sent == Config.HEARTBEAT_NOTIFICATION_AMOUNT:
                        log_it("i", "[HEARTBEAT] Node list notification limit reached, stopping further notifications.")
                        notify_all(f"({Config.NODE_ALIAS}): Node list notification limit reached, stopping further notifications.")
                        return
                    log_it("e", f"[HEARTBEAT] Node is not in the node list for {network}")
                    self.statuses[network]["in_node_list"] = "NOK"
                    notify_all(remove_spacing(f"""
                        ({Config.NODE_ALIAS}): Your node seems not to be in the node list for {network}.
                        Please note that this is not a critical issue, but it may affect your node's performance.
                        If you are sure it should be on node list, please check it manually with:

                        cellframe-node-cli node list -net {network}.
                    """))
                    self.in_node_list_msgs_sent += 1
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    def last_signed_block(self):
        try:
            while is_locked():
                log_it("d", "[HEARTBEAT] Cache is locked, waiting for lock to release...")
                time.sleep(60)
            for network in self.statuses:
                last_run, last_signed_block = get_blocks(network, block_type="all_signed_blocks", heartbeat=True)
                if not last_run:
                    log_it("e", f"[HEARTBEAT] There's no cache data for blocks in network {network}!")
                    continue

                if not last_signed_block:
                    log_it("e", f"[HEARTBEAT] There's no cache data for blocks in network {network}!")
                    continue

                cache_age = datetime.now() - datetime.fromisoformat(last_run)
                log_it("d", f"[HEARTBEAT] Cache age for {network}: {cache_age}")
                if cache_age > timedelta(hours=Config.CACHE_AGE_LIMIT):
                    log_it("e", f"[HEARTBEAT] Cache file for {network} is too old! Last updated: {last_run}. Reporting issue...")
                    notify_all(f"({Config.NODE_ALIAS}): Your blocks cache has not been updated in more than {Config.CACHE_AGE_LIMIT} hours. Please examine your node.")
                    continue

                if last_signed_block:
                    log_it("d", f"[HEARTBEAT] Got block {last_signed_block}")
                    curr_time = datetime.now()
                    block_time = datetime.strptime(last_signed_block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                    time_diff = curr_time - block_time
                    log_it("d", f"Time difference: {time_diff} (current: {curr_time}, block time: {block_time})")
                    if curr_time - block_time > timedelta(hours=Config.HEARTBEAT_BLOCK_AGE):
                        self.statuses[network]['last_signed_block'] = "NOK"
                        log_it("e", f"[HEARTBEAT] Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours!")
                        notify_all(f"({Config.NODE_ALIAS}): Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours!")
                        break
                    else:
                        self.statuses[network]['last_signed_block'] = "OK"
                else:
                    log_it("e", f"[HEARTBEAT] Unable to fetch blocks for {network}")
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

heartbeat = Heartbeat()

def run_heartbeat_check():
    heartbeat.autocollect_status()
    heartbeat.last_signed_block()
    heartbeat.in_node_list()
    log_it("d", f"[HEARTBEAT] Heartbeat check completed.")

    log_it("d", f"[HEARTBEAT] Updated heartbeat statuses: {heartbeat.statuses}")
    if any("NOK" in status.values() for status in heartbeat.statuses.values()):
        log_it("d", f"[HEARTBEAT] has sent {heartbeat.msgs_sent} messages.")
        if heartbeat.msgs_sent == heartbeat.max_msgs_sent:
            if Config.HEARTBEAT_AUTO_RESTART:
                notify_all(f"({Config.NODE_ALIAS}): Node will be restarted because of indicated problems.")
                log_it("i", "[HEARTBEAT] Node will be restarted because of indicated problems.")
                restart_node()
            heartbeat.msgs_sent = 0

        report_heartbeat_errors(heartbeat)
    else:
        log_it("i", "[HEARTBEAT] No issues detected.")
        notify_all("[HEARTBEAT] No issues detected.", channels=["websocket"])

def report_heartbeat_errors(heartbeat):
    try:
        errors = []
        for network, status in heartbeat.statuses.items():
            if status["autocollect_status"] == "NOK":
                errors.append(f"[{network}] Autocollect status seems to be inactive!")
            if status["last_signed_block"] == "NOK":
                errors.append(f"[{network}] Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours!")
                log_it("i", f"[HEARTBEAT] Attempting to resync {network} network...")
                try:
                    change_net_mode(network, "offline")
                    time.sleep(2)
                    change_net_mode(network, "online")
                    time.sleep(2)
                    change_net_mode(network, "resync")
                except Exception as e:
                    log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        if errors:
            error_message = "\n".join(errors)
            log_it("e", f"[HEARTBEAT] Issues detected:\n{error_message}")
            try:
                notify_all(f"({Config.NODE_ALIAS}): {error_message}")
                heartbeat.msgs_sent += 1
            except Exception as e:
                log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        else:
            log_it("i", "[HEARTBEAT] No issues detected.")
            heartbeat.msgs_sent = 0
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
