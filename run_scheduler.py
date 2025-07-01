import traceback
import schedule
from logger import log_it
from config import Config
from cacher import cache_blocks_data, cache_rewards_data
from generators import generate_data
from heartbeat import run_heartbeat_check
from notifications import send_telegram_message, send_email
from updater import install_plugin_update
from thread_launcher import start_thread
from utils import Utils

def run_scheduler(func, scheduled_time, every_x_min=False, run_on_startup=False):
    log_it("d", f"Received func {func}, scheduled_time={scheduled_time}, every_x_min={every_x_min}, run_on_startup={run_on_startup}")
    try:
        scheduler = schedule.Scheduler()
        if run_on_startup:
            log_it("d", f"Running {func.__name__} once on startup.")
            Utils.delay(Config.SCHEDULER_DELAY_ON_STARTUP)
            func()
        if every_x_min:
            scheduler.every(scheduled_time).minutes.do(func)
            log_it("d", f"Scheduling {func.__name__} to run every {scheduled_time} minutes.")
        else:
            scheduler.every().day.at(scheduled_time).do(func)
            log_it("d", f"Scheduling {func.__name__} to run daily at {scheduled_time}.")
        while True:
            scheduler.run_pending()
            Utils.delay(1, logging=False)  # Avoid logging every second
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

def setup_schedules():
    try:
        use_interval_schedule = False
        if Config.STATS_INTERVAL > 0:
            log_it("d", f"Using interval schedule for stats with interval of {Config.STATS_INTERVAL} minutes.")
            if Config.STATS_INTERVAL < 30:
                log_it("e", "STATS_INTERVAL must be at least 30 minutes. Setting it to 30 minutes.")
                Config.STATS_INTERVAL = 30
            use_interval_schedule = True

        start_thread(run_scheduler, cache_blocks_data, Config.CACHE_BLOCKS_INTERVAL, True, True)
        log_it("d", "blocks_caching_schedule started as thread")

        start_thread(run_scheduler, cache_rewards_data, Config.CACHE_REWARDS_INTERVAL, True, True)
        log_it("d", "rewards_caching_schedule started as thread")

        if Config.TELEGRAM_STATS_ENABLED:
            if use_interval_schedule:
                start_thread(
                    run_scheduler,
                    lambda: send_telegram_message(
                        generate_data("telegram.html", return_as_json=False, is_top_level_template=True)
                    ),
                    Config.STATS_INTERVAL,
                    True,
                    False
                )
                log_it("d", f"send_telegram_message_schedule started as thread with interval {Config.STATS_INTERVAL} minutes")
            else:
                start_thread(
                    run_scheduler,
                    lambda: send_telegram_message(
                        generate_data("telegram.html", return_as_json=False, is_top_level_template=True)
                    ),
                    Config.TELEGRAM_STATS_TIME,
                    False,
                    False
                )
                log_it("d", f"send_telegram_message_schedule started as thread with scheduled time {Config.TELEGRAM_STATS_TIME}")

        if Config.EMAIL_STATS_ENABLED:
            if use_interval_schedule:
                start_thread(
                    run_scheduler,
                    lambda: send_email(
                        generate_data("email.html", return_as_json=False, is_top_level_template=True)
                    ),
                    Config.STATS_INTERVAL,
                    True,
                    False
                )
                log_it("d", f"send_email_message_schedule started as thread with interval {Config.STATS_INTERVAL} minutes")
            else:
                start_thread(
                    run_scheduler,
                    lambda: send_email(
                        generate_data("email.html", return_as_json=False, is_top_level_template=True)
                    ),
                    Config.EMAIL_STATS_TIME,
                    False,
                    False
                )
                log_it("d", f"send_email_message_schedule started as thread with scheduled time {Config.EMAIL_STATS_TIME}")

        if Config.AUTO_UPDATE:
            start_thread(
                run_scheduler,
                install_plugin_update,
                120,  # Every 2 hours
                True,
                True
            )
            log_it("d", "auto_updater started as thread every 2 hours")

        start_thread(
            run_scheduler,
            run_heartbeat_check,
            Config.HEARTBEAT_INTERVAL,
            True,
            False
        )
        log_it("d", f"heartbeat_check_schedule started as thread every {Config.HEARTBEAT_INTERVAL} minutes")

    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
