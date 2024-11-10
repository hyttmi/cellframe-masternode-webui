from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from utils import logNotice, logError, cacheBlocks, cacheRewards, funcScheduler, validateTime, validateNum
from generators import generateHTML
from handlers import requestHandler
from mailer import sendMail
from telegram import sendTelegram
from config import Config
import threading, time

def HTTPServer():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=requestHandler)
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{Config.PLUGIN_URI}", handler=handler)
        logNotice("HTTPServer started")
    except Exception as e:
        logError(f"Error: {e}")
    return 0

def init():
    try:
        t = threading.Thread(target=onInit)
        t.setName("onInit")
        t.start()
        logNotice(f"{t.getName()} started")
    except Exception as e:
        logError(f"Error: {e}")
    return 0

def onInit():
    try:
        startup_delay = Config.STARTUP_DELAY
        if validateNum(startup_delay):
            logNotice(f"Delaying startup for {startup_delay} seconds")
            time.sleep(startup_delay)
        else:
            logNotice(f"Delaying startup for 60 seconds")
            time.sleep(60)
        email_stats_enabled = Config.EMAIL_STATS_ENABLED
        email_stats_time = Config.EMAIL_STATS_TIME
        telegram_stats_enabled = Config.TELEGRAM_STATS_ENABLED
        telegram_stats_time = Config.TELEGRAM_STATS_TIME
        cache_rewards_interval = Config.CACHE_REWARDS_INTERVAL
        cache_blocks_interval = Config.CACHE_BLOCKS_INTERVAL

        with ThreadPoolExecutor() as executor:
            logNotice("Submitting HTTPServer to ThreadPool")
            executor.submit(HTTPServer)
            logNotice("Submitting cacheRewards to ThreadPool")
            executor.submit(cacheRewards)  # Run this on startup once to fetch current rewards
            logNotice("Submitting cacheBlocks to ThreadPool")
            executor.submit(cacheBlocks) # Run this on startup once to fetch current signed blocks

            if email_stats_enabled and email_stats_time:
                if validateTime(email_stats_time):
                    logNotice(f"Email sending is activated at {email_stats_time}")
                    executor.submit(sendMail, f"Email sending is activated at {email_stats_time}")
                    executor.submit(funcScheduler, lambda: sendMail(generateHTML("mail.html")), email_stats_time)

            if telegram_stats_enabled and telegram_stats_time:
                if validateTime(telegram_stats_time):
                    logNotice(f"Telegram sending is activated at {telegram_stats_time}")
                    executor.submit(sendTelegram, f"Telegram sending is activated at {telegram_stats_time}")
                    executor.submit(funcScheduler, lambda: sendTelegram(generateHTML("telegram.html")), telegram_stats_time)

            if validateNum(cache_rewards_interval):
                if cache_rewards_interval < 10:
                    logError("Rewards caching time is below 10 minutes which is not recommended as it uses lots of CPU. Consider higher value.")
                executor.submit(funcScheduler, cacheRewards, False, cache_rewards_interval)

            if validateNum(cache_blocks_interval):
                executor.submit(funcScheduler, cacheBlocks, False, cache_blocks_interval)
    except Exception as e:
        logError(f"Error: {e}")

def deinit():
    logNotice("stopped")
    return 0
