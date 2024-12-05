try:
    import requests
    from utils import log_it
    from config import Config
except ImportError as e:
    log_it("e", f"ImportError: {e}")

def send_telegram_message(message):
    missing_configs = []

    if not Config.TELEGRAM_API_TOKEN:
        missing_configs.append("telegram_api_key")
    if not Config.TELEGRAM_CHAT_ID:
        missing_configs.append("telegram_chat_id")

    if missing_configs:
        for config in missing_configs:
            log_it("e", f"{config} is not set!")
        return
            
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_API_TOKEN}/sendMessage"
        payload = {
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': "HTML"
        }
        response = requests.post(url, params=payload)

        if response.status_code == 200:
            log_it("i", "Telegram message sent!")
        else:
            log_it("i", f"Sending Telegram message failed! Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_it("e", f"Error: {e}")
