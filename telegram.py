import requests
from utils import getConfigValue, logError, logNotice

def sendTelegram(text):
    API_TOKEN = getConfigValue("webui", "telegram_api_key")
    CHAT_ID = getConfigValue("webui", "telegram_chat_id")
    missing_configs = []

    if API_TOKEN is None:
        missing_configs.append("telegram_api_key")
    if CHAT_ID is None:
        missing_configs.append("telegram_chat_id")

    if missing_configs:
        for config in missing_configs:
            logError(f"{config} is not set!")
        return
            
    try:
        url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
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
