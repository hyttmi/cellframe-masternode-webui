from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config
from logger import log_it
import requests, smtplib, traceback
from time import sleep
from websocket_server import ws_broadcast_msg

def send_telegram_message(message):
    missing_configs = []

    if not Config.TELEGRAM_API_TOKEN and not Config.TELEGRAM_BOT_TOKEN:
        missing_configs.append("telegram_api_key or telegram_bot_key")
    if not Config.TELEGRAM_CHAT_ID:
        missing_configs.append("telegram_chat_id")

    if missing_configs:
        for config in missing_configs:
            log_it("e", f"{config} is not set!")
        return

    try:
        if Config.TELEGRAM_BOT_TOKEN: # Higher priority to this
            url = "https://cfwebui.pqcc.fi/send_message"
            if isinstance(Config.TELEGRAM_BOT_TOKEN, list): # stats to all chat_id's
                log_it("d", f"Got list of tokens: {Config.TELEGRAM_BOT_TOKEN}")
                for chat_id in Config.TELEGRAM_BOT_TOKEN:
                    payload = {
                        'plugin_id': chat_id,
                        'message': message
                    }
                    response = requests.post(url, json=payload)
                    sleep(1) # To avoid hammering
                    if response.status_code == 200:
                        log_it("i", f"Telegram message sent via server to chat id {chat_id}!")
                    else:
                        log_it("e", f"Sending Telegram message via server failed! Status code: {response.status_code}, Response: {response.text}")
            else:
                log_it("d", f"Got token: {Config.TELEGRAM_BOT_TOKEN}")
                payload = {
                    'plugin_id': Config.TELEGRAM_BOT_TOKEN,
                    'message': message
                }
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    log_it("i", f"Telegram message sent via server to chat id {Config.TELEGRAM_BOT_TOKEN}")
                else:
                    log_it("e", f"Sending Telegram message via server failed! Status code: {response.status_code}, Response: {response.text}")
        elif Config.TELEGRAM_API_TOKEN:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_API_TOKEN}/sendMessage"
            payload = {
                'chat_id': Config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': "HTML"
            }
            response = requests.post(url, params=payload)

            if response.status_code == 200:
                log_it("i", "Telegram message sent via API!")
                return True
            else:
                log_it("e", f"Sending Telegram message failed! Status code: {response.status_code}, Response: {response.text}")
                return False
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())

def send_email(msg):
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT
    use_ssl = Config.EMAIL_USE_SSL
    use_tls = Config.EMAIL_USE_TLS
    smtp_user = Config.SMTP_USER
    smtp_password = Config.SMTP_PASSWORD
    email_recipients = Config.EMAIL_RECIPIENTS
    email_subject = Config.EMAIL_SUBJECT

    missing_configs = []

    if not smtp_user:
        missing_configs.append("SMTP_USER")
    if not smtp_password:
        missing_configs.append("SMTP_PASSWORD")
    if not email_recipients:
        missing_configs.append("EMAIL_RECIPIENTS")
    if not smtp_server:
        missing_configs.append("SMTP_SERVER")
    if not smtp_port:
        missing_configs.append("SMTP_PORT")

    if missing_configs:
        for config in missing_configs:
            log_it("e", f"{config} is not set!")
        return False

    if not use_ssl and not use_tls:
        log_it("e", "SSL or TLS must be enabled for email sending!")
        return False

    email_msg = MIMEMultipart("alternative")
    email_msg["From"] = smtp_user
    email_msg["To"] = ', '.join(email_recipients)
    email_msg["Subject"] = email_subject
    part = MIMEText(msg, "html")
    email_msg.attach(part)

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, email_recipients, email_msg.as_string())
        server.close()
        log_it("i", "Email sent!")
        return True
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
        return False

def notify_all(message, channels=None):
    if channels is None:
        channels = ["telegram", "email", "websocket"] # All by default
    try:
        if "telegram" in channels:
            if Config.TELEGRAM_STATS_ENABLED:
                if send_telegram_message(message):
                    log_it("i", "Telegram notification sent!")
            else:
                log_it("e", "Telegram notifications are disabled in the configuration.")
        if "email" in channels:
            if Config.EMAIL_STATS_ENABLED:
                if send_email(message):
                    log_it("i", "Email notification sent!")
            else:
                log_it("e", "Email notifications are disabled in the configuration.")
        if "websocket" in channels:
            if Config.WEBSOCKET_SERVER_RUNNING:
                ws_broadcast_msg(message)
            else:
                log_it("e", "WebSocket server is not running.")
        log_it("i", f"Notification sent: {message}")
    except Exception as e:
        log_it("e", f"An error occurred: {e}", exc=traceback.format_exc())
