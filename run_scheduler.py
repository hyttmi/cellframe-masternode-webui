import schedule
from logger import log_it
import time

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
        log_it("e", f"Error: {e}")
