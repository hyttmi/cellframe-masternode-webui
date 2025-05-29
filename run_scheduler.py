from cacher import cache_blocks_data, cache_rewards_data
from concurrent.futures import ThreadPoolExecutor
from config import Config
from generators import generate_data
from heartbeat import run_heartbeat_check
from logger import log_it
from notifications import notify_all, send_telegram_message, send_email
from updater import install_plugin_update
import time, schedule

def run_scheduler(func, scheduled_time, every_min=False, run_on_startup=False):
    log_it("d", f"Received func {func}, scheduled_time={scheduled_time}, every_min={every_min}, run_on_startup={run_on_startup}")
    try:
        scheduler = schedule.Scheduler()
        if run_on_startup:
            log_it("d", f"Running {func} once on startup.")
            time.sleep(Config.SCHEDULER_DELAY_ON_STARTUP)
            func()
        if every_min:
            scheduler.every(scheduled_time).minutes.do(func)
            log_it("d", f"Scheduling {func.__name__} to run every {scheduled_time} minutes.")
        else:
            scheduler.every().day.at(scheduled_time).do(func)
            log_it("d", f"Scheduling {func.__name__} to run daily at {scheduled_time}.")
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except Exception as e:
        log_it("e", "An error occurred", exc=e)

def setup_schedules():
    try:
        with ThreadPoolExecutor() as executor:
            futures = {}
            futures['blocks_caching_schedule'] = executor.submit(
                run_scheduler,
                cache_blocks_data,
                Config.CACHE_BLOCKS_INTERVAL,
                every_min=True,
                run_on_startup=True
            )
            log_it("d", "blocks_caching_schedule submitted to ThreadPool")

            futures['rewards_caching_schedule'] = executor.submit(
                run_scheduler,
                cache_rewards_data,
                Config.CACHE_REWARDS_INTERVAL,
                every_min=True,
                run_on_startup=True
            )
            log_it("d", "rewards_caching_schedule submitted to ThreadPool")

            if Config.TELEGRAM_STATS_ENABLED:
                if Config.STATS_INTERVAL > 0:
                    futures['send_telegram_message_schedule'] = executor.submit(
                        run_scheduler,
                        lambda: send_telegram_message(
                            generate_data("telegram.html", return_as_json=False, is_top_level_template=True)
                        ),
                        Config.STATS_INTERVAL,
                        every_min=True,
                        run_on_startup=False
                    )
                    log_it("d", f"send_telegram_message_schedule submitted to ThreadPool with interval of {Config.STATS_INTERVAL} minutes")
                else:
                    futures['send_telegram_message_schedule'] = executor.submit(
                        run_scheduler,
                        lambda: send_telegram_message(
                            generate_data("telegram.html", return_as_json=False, is_top_level_template=True)
                        ),
                        Config.TELEGRAM_STATS_TIME,
                        every_min=False,
                        run_on_startup=False
                    )
                    log_it("d", "send_telegram_message_schedule submitted to ThreadPool with scheduled time of {Config.TELEGRAM_STATS_TIME}")

            if Config.EMAIL_STATS_ENABLED:
                if Config.STATS_INTERVAL > 0:
                    if Config.STATS_INTERVAL < 30:
                        log_it("e", "STATS_INTERVAL must be at least 30 minutes. Setting it to 30 minutes.")
                        Config.STATS_INTERVAL = 30
                    futures['send_email_message_schedule'] = executor.submit(
                        run_scheduler,
                        lambda: send_email(
                            generate_data("email.html", return_as_json=False, is_top_level_template=True)
                        ),
                        Config.STATS_INTERVAL,
                        every_min=True,
                        run_on_startup=False
                    )
                    log_it("d", f"send_email_message_schedule submitted to ThreadPool with interval of {Config.STATS_INTERVAL} minutes")
                else:
                    log_it("d", f"send_email_message_schedule submitted to ThreadPool with interval of {Config.STATS_INTERVAL} minutes")
                    futures['send_email_message_schedule'] = executor.submit(
                        run_scheduler,
                        lambda: send_email(
                            generate_data("email.html", return_as_json=False, is_top_level_template=True)
                        ),
                        Config.EMAIL_STATS_TIME,
                        every_min=False,
                        run_on_startup=False
                    )
                    log_it("d", f"send_email_message_schedule submitted to ThreadPool with scheduled time of {Config.EMAIL_STATS_TIME}")

            if Config.AUTO_UPDATE:
                futures['auto_updater'] = executor.submit(
                    run_scheduler,
                    lambda: install_plugin_update(),
                    120,  # Every 2 hours
                    every_min=True,
                    run_on_startup=True
                )
                log_it("d", "auto_updater submitted to ThreadPool to run every 2 hours")

            futures['heartbeat_check_schedule'] = executor.submit(
                run_scheduler,
                run_heartbeat_check,
                Config.HEARTBEAT_INTERVAL,
                every_min=True,
                run_on_startup=False
            )
            log_it("d", f"heartbeat_check_schedule submitted to ThreadPool to run every {Config.HEARTBEAT_INTERVAL} minutes.")

            futures['notify_user'] = executor.submit(
                notify_all,
                f"{Config.PLUGIN_NAME} started!"
                )
            log_it("d", "notify_user submitted to ThreadPool")

    except Exception as e:
        log_it("e", "An error occurred", exc=e)