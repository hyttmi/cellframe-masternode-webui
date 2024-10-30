import requests
from utils import logError, logNotice
from config import Config

def sendTelegram(text):
    missing_configs = []

    if Config.TELEGRAM_API_TOKEN is None:
        missing_configs.append("telegram_api_key")
    if Config.TELEGRAM_CHAT_ID is None:
        missing_configs.append("telegram_chat_id")

    if missing_configs:
        for config in missing_configs:
            logError(f"{config} is not set!")
        return
            
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_API_TOKEN}/sendMessage"
        payload = {
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': "HTML"
        }
        res = requests.post(url, params=payload)

        if res.status_code == 200:
            logNotice("Telegram message sent!")
        else:
            logError(f"Sending Telegram message failed! Status code: {res.status_code}, Response: {res.text}")
    except Exception as e:
        logError(f"Error: {e}")
