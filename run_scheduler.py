from cacher import cache_blocks_data, cache_rewards_data
from concurrent.futures import ThreadPoolExecutor
from config import Config
from generators import generate_data
from heartbeat import run_heartbeat_check
from logger import log_it
from notifications import send_telegram_message, send_email
from updater import install_plugin_update
import schedule, time

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
                futures['send_telegram_message_notification'] = executor.submit(
                    send_telegram_message,
                    f"Telegram sending scheduled at {Config.TELEGRAM_STATS_TIME} from {Config.NODE_ALIAS}"
                )
                log_it("d", "send_telegram_message_notification submitted to ThreadPool")

                futures['send_telegram_message_schedule'] = executor.submit(
                    run_scheduler,
                    lambda: send_telegram_message(
                        generate_data("telegram.html", return_as_json=False, is_top_level_template=True)
                    ),
                    Config.TELEGRAM_STATS_TIME,
                    every_min=False,
                    run_on_startup=False
                )
                log_it("d", "send_telegram_message_schedule submitted to ThreadPool")

            if Config.EMAIL_STATS_ENABLED:
                futures['send_email_message_notification'] = executor.submit(
                    send_email,
                    f"Email sending scheduled at {Config.EMAIL_STATS_TIME}  from {Config.NODE_ALIAS}"
                )
                log_it("d", "send_email_message_notification submitted to ThreadPool")

                futures['send_email_message_schedule'] = executor.submit(
                    run_scheduler,
                    lambda: send_email(
                        generate_data("email.html", return_as_json=False, is_top_level_template=True)
                    ),
                    Config.EMAIL_STATS_TIME,
                    every_min=False,
                    run_on_startup=False
                )
                log_it("d", "send_email_message_schedule submitted to ThreadPool")

            if Config.AUTO_UPDATE:
                futures['auto_updater'] = executor.submit(
                    run_scheduler,
                    lambda: install_plugin_update(),
                    120,  # Every 2 hours
                    every_min=True,
                    run_on_startup=True
                )
                log_it("d", "auto_updater submitted to ThreadPool")

            futures['heartbeat_check_schedule'] = executor.submit(
                run_scheduler,
                run_heartbeat_check,
                15,
                every_min=True,
                run_on_startup=False
            )
            log_it("d", "heartbeat_check_schedule submitted to ThreadPool")

            for name in futures:
                log_it("d", f"{name} submitted to ThreadPool")

    except Exception as e:
        log_it("e", "An error occurred", exc=e)