from networkutils import (
    get_active_networks,
    get_network_config,
    get_autocollect_status,
    get_blocks,
    change_net_mode,
    is_node_in_node_list
)
from utils import Utils
from cacher import is_locked
from config import Config, Globals
from logger import log_it
from notifications import notify_all
from datetime import datetime, timedelta
import traceback

class Heartbeat:
    def __init__(self):
        log_it("d", "[HEARTBEAT] Initializing heartbeat...")
        self.max_msgs_sent = Config.HEARTBEAT_NOTIFICATION_AMOUNT
        self.statuses = {
            network: {
                "autocollect_status": "Unknown",
                "last_signed_block": "Unknown",
                "in_node_list": "Unknown",
                "msgs_sent": 0,
                "in_node_list_msgs_sent": 0
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
                    log_it("e", f"[HEARTBEAT] Autocollect status seems to be inactive for {network}!")
                    notify_all(f"({Config.NODE_ALIAS}): Autocollect status seems to be inactive for {network}!")
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    def in_node_list(self):
        try:
            for network in self.statuses:
                in_node_list = is_node_in_node_list(network)
                if in_node_list:
                    log_it("d", f"[HEARTBEAT] Node is in the node list for {network}")
                    self.statuses[network]["in_node_list"] = "OK"
                    self.statuses[network]["in_node_list_msgs_sent"] = 0
                else:
                    if self.statuses[network]["in_node_list_msgs_sent"] >= self.max_msgs_sent:
                        log_it("i", f"[HEARTBEAT] Node list notification limit reached for {network}, stopping further notifications.")
                        continue
                    log_it("e", f"[HEARTBEAT] Node is not in the node list for {network}")
                    self.statuses[network]["in_node_list"] = "NOK"
                    self.statuses[network]["in_node_list_msgs_sent"] += 1
                    remaining = self.max_msgs_sent - self.statuses[network]["in_node_list_msgs_sent"]
                    notify_all(Utils.remove_spacing(f"""
                        ({Config.NODE_ALIAS}): Your node seems not to be in the node list for {network}. Please note that this is not a critical issue, but it may affect your node's performance.

                        If you are sure it should be on node list, please check it manually with the command:

                            cellframe-node-cli node list -net {network}

                        {f"You will not receive further reminders about this." if remaining == 0 else f"This is reminder {self.statuses[network]['in_node_list_msgs_sent']} of {self.max_msgs_sent}."}
                    """))
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

    def last_signed_block(self):
        try:
            while is_locked():
                log_it("d", "[HEARTBEAT] Cache is locked, waiting for lock to release...")
                Utils.delay(60)
            for network in self.statuses:
                last_run, last_signed_block = get_blocks(network, block_type="all_signed_blocks", heartbeat=True)
                if not last_run or not last_signed_block:
                    log_it("e", f"[HEARTBEAT] No cache data for blocks in network {network}!")
                    continue

                cache_age = datetime.now() - datetime.fromisoformat(last_run)
                log_it("d", f"[HEARTBEAT] Cache age for {network}: {cache_age}")
                if cache_age > timedelta(hours=Config.CACHE_AGE_LIMIT):
                    log_it("e", f"[HEARTBEAT] Cache file for {network} is too old! Last updated: {last_run}. Reporting issue...")
                    notify_all(f"({Config.NODE_ALIAS}): Your blocks cache has not been updated in more than {Config.CACHE_AGE_LIMIT} hours. Please examine your node.")
                    continue

                block_time = datetime.strptime(last_signed_block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                time_diff = datetime.now() - block_time
                log_it("d", f"[HEARTBEAT] Time difference for {network}: {time_diff}")
                if time_diff > timedelta(hours=Config.HEARTBEAT_BLOCK_AGE):
                    self.statuses[network]["last_signed_block"] = "NOK"
                    log_it("e", f"[HEARTBEAT] Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours for {network}! Reporting issue...")
                    notify_all(f"({Config.NODE_ALIAS}): Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours on {network}!")
                else:
                    self.statuses[network]["last_signed_block"] = "OK"
        except Exception as e:
            log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

heartbeat = Heartbeat()

def run_heartbeat_check():
    heartbeat.autocollect_status()
    heartbeat.last_signed_block()
    heartbeat.in_node_list()
    log_it("d", f"[HEARTBEAT] Heartbeat check completed.")
    log_it("d", f"[HEARTBEAT] Updated heartbeat statuses: {heartbeat.statuses}")

    problems = any(
        any(status.get(key) == "NOK" for key in ("autocollect_status", "last_signed_block", "in_node_list"))
        for status in heartbeat.statuses.values()
    )

    if problems:
        for network in heartbeat.statuses:
            report_heartbeat_errors(heartbeat, network)
    else:
        log_it("i", "[HEARTBEAT] No issues detected.")
        notify_all("[HEARTBEAT] No issues detected.", channels=["websocket"])

def report_heartbeat_errors(heartbeat, network):
    try:
        status = heartbeat.statuses[network]
        errors = []

        if status["autocollect_status"] == "NOK":
            errors.append(f"[{network}] Autocollect status seems to be inactive!")
        if status["last_signed_block"] == "NOK":
            errors.append(f"[{network}] Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours!")
            log_it("i", f"[HEARTBEAT] Attempting to resync {network} network...")
            try:
                change_net_mode(network, "offline")
                Utils.delay(2)
                change_net_mode(network, "online")
                Utils.delay(2)
                change_net_mode(network, "resync")
            except Exception as e:
                log_it("e", f"An error occurred while resyncing {network}: {e}", exc=traceback.format_exc())

        if errors:
            error_message = "\n".join(errors)
            log_it("e", f"[HEARTBEAT] Issues detected for {network}:\n{error_message}")
            try:
                notify_all(f"({Config.NODE_ALIAS}): {error_message}")
                status["msgs_sent"] += 1
                if status["msgs_sent"] >= heartbeat.max_msgs_sent and Config.HEARTBEAT_AUTO_RESTART:
                    if Globals.IS_RUNNING_AS_SERVICE:
                        log_it("i", f"[HEARTBEAT] Restarting node due to repeated issues on {network}.")
                        notify_all(f"({Config.NODE_ALIAS}): Restarting node due to repeated issues on {network}.")
                        Utils.restart_node()
            except Exception as e:
                log_it("e", f"An error occurred during notification for {network}: {e}", exc=traceback.format_exc())
        else:
            log_it("i", f"[HEARTBEAT] No issues detected for {network}.")
            status["msgs_sent"] = 0
    except Exception as e:
        log_it("e", f"An error occurred in report_heartbeat_errors for {network}: {e}", exc=traceback.format_exc())
