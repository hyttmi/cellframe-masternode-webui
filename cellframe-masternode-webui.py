from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from handlers import *
from utils import *
from mailer import sendMail
from telegram import sendTelegram
import threading

def HTTPServer():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=requestHandler)
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{PLUGIN_URI}", handler=handler)
        logNotice("started")
    except Exception as e:
        logError(f"Error: {e}")
    return 0

def init():
    t = threading.Thread(target=startInitialization)
    t.start()
    return 0

def startInitialization():
    email_stats_enabled = getConfigValue("webui", "email_stats", default=False)
    email_stats_time = getConfigValue("webui", "email_time")
    telegram_stats_enabled = getConfigValue("webui", "telegram_stats", default=False)
    telegram_stats_time = getConfigValue("webui", "telegram_stats_time")
    cache_rewards = getConfigValue("webui", "cache_rewards", default=False)
    cache_rewards_time = getConfigValue("webui", "cache_rewards_time")
            
    with ThreadPoolExecutor() as executor:
        executor.submit(HTTPServer)
        
        if email_stats_enabled and validateTime(email_stats_time):
            logNotice(f"Email sending is activated at {email_stats_time}")
            executor.submit(sendMail, f"Email sending is activated at {email_stats_time}")
            executor.submit(funcScheduler, lambda: sendMail(generateHTML("mail.html")), email_stats_time)
        
        if telegram_stats_enabled and validateTime(telegram_stats_time):
            logNotice(f"Telegram sending is activated at {telegram_stats_time}")
            executor.submit(sendTelegram, f"Telegram sending is activated at {telegram_stats_time}")
            executor.submit(funcScheduler, lambda: sendTelegram(generateHTML("telegram.html")), telegram_stats_time)
        
        if cache_rewards and validateNum(cache_rewards_time):
            if cache_rewards_time < 10:
                logError("Rewards caching time is below 10 minutes which is not recommended as it uses lots of CPU. Consider higher value.")
            executor.submit(cacheRewards) # Run once on startup, then with the timer as we know that both settings are set
            executor.submit(funcScheduler, cacheRewards, False, cache_rewards_time)

def deinit():
    logNotice("stopped")
    return 0
