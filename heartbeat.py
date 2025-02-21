from networkutils import (
    get_active_networks,
    get_network_config,
    get_autocollect_status,
    get_blocks,
    get_node_data
)
from utils import restart_node
from cacher import is_locked
from config import Config
from logger import log_it
from notifications import send_email, send_telegram_message
from datetime import datetime, timedelta
import time

class Heartbeat:
    def __init__(self):
        self.max_sent_msgs = Config.HEARTBEAT_NOTIFICATION_AMOUNT
        self.msgs_sent = 0
        self.statuses = {
            network: {
                "autocollect_status": "Unknown",
                "last_signed_block": "Unknown",
                "is_active_in_consensus": "Unknown"
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

    def is_active_in_consensus(self):
        try:
            for network in self.statuses:
                active_status_list = get_node_data(network, only_my_node=True)
                if active_status_list:
                    active_status = active_status_list[0]
                    is_active = active_status.get("active", "").lower() == "true"
                else:
                    is_active = False
                self.statuses[network]['is_active'] = "OK" if is_active else "NOK"
                if not is_active:
                    log_it("e", "[HEARTBEAT] Node seems to be inactive in consensus.")
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

    def last_signed_block(self):
        try:
            while is_locked():
                log_it("d", "[HEARTBEAT] Cache is locked, waiting for lock to release...")
                time.sleep(60)
            for network in self.statuses:
                last_signed_block = get_blocks(network, block_type="all_signed_blocks", heartbeat=True)
                if last_signed_block:
                    log_it("d", f"[HEARTBEAT] Got block {last_signed_block}")
                    curr_time = datetime.now()
                    block_time = datetime.strptime(last_signed_block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                    time_diff = curr_time - block_time
                    log_it("d", f"Time difference: {time_diff} (current: {curr_time}, block time: {block_time})")
                    if curr_time - block_time > timedelta(seconds=Config.HEARTBEAT_BLOCK_AGE):
                        self.statuses[network]['last_signed_block'] = "NOK"
                        log_it("e", f"[HEARTBEAT] Last signed block is older than 10 hours!")
                        break
                    else:
                        self.statuses[network]['last_signed_block'] = "OK"
                else:
                    log_it("e", f"Unable to fetch blocks for {network}")
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

heartbeat = Heartbeat()

def run_heartbeat_check():
    heartbeat.autocollect_status(),
    heartbeat.last_signed_block(),
    heartbeat.is_active_in_consensus()

    log_it("d", f"[HEARTBEAT] Updated heartbeat statuses: {heartbeat.statuses}")
    if any("NOK" in status.values() for status in heartbeat.statuses.values()):
        heartbeat.msgs_sent += 1
        log_it("d", f"[HEARTBEAT] has sent {heartbeat.msgs_sent} messages.")
        if heartbeat.msgs_sent == heartbeat.max_sent_msgs:
            if Config.TELEGRAM_STATS_ENABLED:
                send_telegram_message(f"({Config.NODE_ALIAS}): Node will be restarted because of indicated problems.")
            if Config.EMAIL_STATS_ENABLED:
                send_email(f"({Config.NODE_ALIAS}) Heartbeat alert", "Node will be restarted because of indicated problems.")
            log_it("i", "[HEARTBEAT] Node will be restarted because of indicated problems.")
            restart_node()
        report_heartbeat_errors(heartbeat)
    else:
        log_it("d", "[HEARTBEAT] No issues detected.")

def report_heartbeat_errors(heartbeat):
    errors = []
    for network, status in heartbeat.statuses.items():
        if status["autocollect_status"] == "NOK":
            errors.append(f"[{network}] Autocollect status seems to be inactive!")
        if status["last_signed_block"] == "NOK":
            errors.append(f"[{network}] Last signed block is older than {Config.HEARTBEAT_BLOCK_AGE} hours!")
        if status['is_active_in_consensus'] == "NOK":
            errors.append(f"[{network}] Node seems to be inactive in consensus!")
    if errors:
        error_message = "\n".join(errors)
        log_it("e", f"[HEARTBEAT] Issues detected:\n{error_message}")

        if Config.TELEGRAM_STATS_ENABLED:
            send_telegram_message(f"({Config.NODE_ALIAS}): {error_message}")

        if Config.EMAIL_STATS_ENABLED:
            send_email(f"({Config.NODE_ALIAS}) Heartbeat alert", error_message)
