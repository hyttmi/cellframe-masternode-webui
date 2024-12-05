try:
    import schedule, inspect
    from logger import log_it
    import time
    from cacher import cache_blocks_data, cache_rewards_data
    from telegram import send_telegram_message
    from generators import generate_html
    from config import Config
    from concurrent.futures import ThreadPoolExecutor
except Exception as e:
    log_it("e", f"ImportError: {e}")

def run_scheduler(func, scheduled_time, every_min=False, run_on_startup=False):
    log_it("d", f"Received func {func}, scheduled_time={scheduled_time}, every_min={every_min}")
    try:
        scheduler = schedule.Scheduler()
        if run_on_startup:
            log_it("i", f"Running {func} once on startup.")
            func()
        if every_min:
            scheduler.every(scheduled_time).minutes.do(func)
            log_it("i", f"Scheduling {func.__name__} to run every {scheduled_time} minutes.")
        else:
            scheduler.every().day.at(scheduled_time).do(func)
            log_it("i", f"Scheduling {func.__name__} to run daily at {scheduled_time}.")
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
                    executor.submit(lambda: run_scheduler(lambda: send_telegram_message(f"Telegram sending scheduled at {Config.TELEGRAM_STATS_TIME}"), Config.TELEGRAM_STATS_TIME, every_min=False, run_on_startup=True)),
                'send_telegram_message_schedule': 
                    executor.submit(lambda: run_scheduler(lambda: send_telegram_message(generate_html("telegram.html")), Config.TELEGRAM_STATS_TIME, every_min=False, run_on_startup=False))
            }
            for name, future in futures.items():
                log_it("i", f"{name} submitted to ThreadPool")

    except Exception as e:
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
