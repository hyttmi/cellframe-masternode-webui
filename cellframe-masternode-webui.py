from pycfhelpers.node.http.simple import CFSimpleHTTPServer, CFSimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from handlers import *
from utils import *
from mailer import sendMail
from telegram import sendTelegram

def HTTPServer():
    try:
        handler = CFSimpleHTTPRequestHandler(methods=["GET"], handler=requestHandler)
        CFSimpleHTTPServer().register_uri_handler(uri=f"/{PLUGIN_URI}", handler=handler)
        logNotice("started")
    except Exception as e:
        logError(f"Error: {e}")
    return 0

def test():
    print("yes")

def init():
    email_stats_enabled = getConfigValue("webui", "email_stats")
    email_stats_time = getConfigValue("webui", "email_time")
    telegram_stats_enabled = getConfigValue("webui", "telegram_stats")
    telegram_stats_time = getConfigValue("webui", "telegram_stats_time")
    cache_rewards = getConfigValue("webui", "cache_rewards", default=False)
            
    with ThreadPoolExecutor() as executor:
        executor.submit(HTTPServer)
        if email_stats_enabled is not None and validateTime(email_stats_time):
            logNotice(f"Email sending is activated at {email_stats_time}")
            executor.submit(sendMail, f"Email sending is activated at {email_stats_time}")
            executor.submit(funcScheduler, lambda: sendMail(generateHTML("mail.html")), email_stats_time)
        if telegram_stats_enabled is not None and validateTime(telegram_stats_time):
            executor.submit(sendTelegram, f"Telegram sending is activated at {telegram_stats_time}")
            logNotice(f"Telegram sending is activated at {telegram_stats_time}")
            executor.submit(funcScheduler, lambda: sendTelegram(generateHTML("telegram.html")), telegram_stats_time)
    with ProcessPoolExecutor() as pexecutor: # Use ProcessPoolExecutor for CPU bound tasks, not sure if it's the right choice :)
        if cache_rewards:
            pexecutor.submit(cacheRewards)
    return 0

def deinit():
    logNotice("stopped")
    return 0
