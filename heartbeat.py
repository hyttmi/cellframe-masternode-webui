from networkutils import (
    get_active_networks,
    get_network_config,
    get_autocollect_status,
    get_blocks
)
from cacher import is_locked
from config import Config
from logger import log_it
from notifications import send_email, send_telegram_message
from datetime import datetime, timedelta
import time

class Heartbeat:
    def __init__(self):
        msg_sent = False
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
            while is_locked():
                log_it("d", "[HEARTBEAT] Cache is locked, waiting for lock to release...")
                time.sleep(10) # Don't do anything if we're caching...
            for network in self.statuses:
                signed_blocks = get_blocks(network, heartbeat=True)
                log_it("d", signed_blocks)
                curr_time = datetime.now()
                for block in signed_blocks:
                    log_it("d", block)
                    block_time = datetime.strptime(block["ts_created"], "%a, %d %b %Y %H:%M:%S")
                    if curr_time - block_time > timedelta(hours=12):
                        self.statuses[network]['signed_blocks'] = "NOK"
                        log_it("e", f"[HEARTBEAT] Signed block {block['tx_hash']} is older than 6 hours!")
                        break
                else:
                    self.statuses[network]['signed_blocks'] = "OK"
        except Exception as e:
            log_it("e", "An error occurred", exc=e)

def run_heartbeat_check():
    heartbeat = Heartbeat()
    heartbeat.autocollect_status()
    heartbeat.last_signed_block()
    log_it("d", f"[HEARTBEAT] Updated heartbeat statuses: {heartbeat.statuses}")

    if not heartbeat.msg_sent and any(
        status["autocollect_status"] == "NOK" or status["signed_blocks"] == "NOK"
        for status in heartbeat.statuses.values()
    ):
        report_heartbeat_errors(heartbeat)
        heartbeat.msg_sent = True
    else:
        log_it("d", "[HEARTBEAT] No issues detected or notification already sent.")

def report_heartbeat_errors(heartbeat):
    if not (Config.TELEGRAM_STATS_ENABLED or Config.EMAIL_STATS_ENABLED):
        log_it("d", "[HEARTBEAT] Telegram and / or email sending is not enabled, can't send message!")
        return

    errors = []
    for network, status in heartbeat.statuses.items():
        if status["autocollect_status"] == "NOK":
            errors.append(f"[{network}] Autocollect status: NOK")
        if status["signed_blocks"] == "NOK":
            errors.append(f"[{network}] Signed blocks are too old!")

    if errors:
        error_message = "\n".join(errors)
        log_it("e", f"[HEARTBEAT] Issues detected:\n{error_message}")

        if Config.TELEGRAM_STATS_ENABLED:
            send_telegram_message(error_message)

        if Config.EMAIL_STATS_ENABLED:
            send_email("Heartbeat Alert", error_message)
