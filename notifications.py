from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from config import Config
from logger import log_it
import requests

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
            log_it("e", f"Sending Telegram message failed! Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_it("e", "An error occurred", exc=e)

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
        return

    if not use_ssl and not use_tls:
        log_it("e", "SSL or TLS must be enabled for email sending!")
        return

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
    except Exception as e:
        log_it("e", "An error occurred", exc=e)
        log_it("e", f"Error sending email: {e}")