from cacher import cache_blocks_data, cache_rewards_data
from concurrent.futures import ThreadPoolExecutor
from config import Config
from emailer import send_email
from generators import generate_data
from logger import log_it
from telegram import send_telegram_message
import schedule, inspect, time

def run_scheduler(func, scheduled_time, every_min=False, run_on_startup=False):
    log_it("d", f"Received func {func}, scheduled_time={scheduled_time}, every_min={every_min}")
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
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")

def setup_schedules():
    try:
        with ThreadPoolExecutor() as executor:
            futures = {
                'blocks_caching_schedule': 
                    executor.submit(lambda: run_scheduler(cache_blocks_data, Config.CACHE_BLOCKS_INTERVAL, every_min=True, run_on_startup=True)),
                'rewards_caching_schedule': 
                    executor.submit(lambda: run_scheduler(cache_rewards_data, Config.CACHE_REWARDS_INTERVAL, every_min=True, run_on_startup=True)),
                'send_telegram_message_notification': 
                    executor.submit(lambda: send_telegram_message(f"Telegram sending scheduled at {Config.TELEGRAM_STATS_TIME}")),
                'send_telegram_message_schedule': 
                    executor.submit(lambda: run_scheduler(lambda: send_telegram_message(generate_data("telegram.html", return_as_json=False, is_top_level_template=True)), Config.TELEGRAM_STATS_TIME, every_min=False, run_on_startup=False)),
                'send_email_message_notification':
                    executor.submit(lambda: send_email(f"Email sending scheduled at {Config.EMAIL_STATS_TIME}")),
                'send_email_message_schedule':
                    executor.submit(lambda: run_scheduler(lambda: send_email(generate_data("email.html", return_as_json=False, is_top_level_template=True)), Config.EMAIL_STATS_TIME, every_min=False, run_on_startup=False)),
            }
            for name in futures:
                log_it("d", f"{name} submitted to ThreadPool")
    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")

