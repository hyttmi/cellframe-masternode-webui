try:
    import schedule
    from logger import log_it
    import time
    from cacher import cache_blocks_data, cache_rewards_data
    from config import Config
    from concurrent.futures import ThreadPoolExecutor
except Exception as e:
    log_it("e", f"ImportError: {e}")

def run_scheduler(func, scheduled_time, every_min=False):
    log_it("d", f"Received func {func}, scheduled_time={scheduled_time}, every_min={every_min}")
    try:
        scheduler = schedule.Scheduler()
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
        log_it("e", f"Error in run_scheduler: {e}")

def setup_schedules():
    try:
        with ThreadPoolExecutor() as executor:
            futures = {
                'blocks_caching': executor.submit(lambda: run_scheduler(cache_blocks_data, Config.CACHE_BLOCKS_INTERVAL, every_min=True)),
                'rewards_caching': executor.submit(lambda: run_scheduler(cache_rewards_data, Config.CACHE_REWARDS_INTERVAL, every_min=True))
            }
            for name, future in futures.items():
                log_it("i", f"{name} submitted to ThreadPool")

    except Exception as e:
        log_it("e", f"Error in setup_schedules: {e}")