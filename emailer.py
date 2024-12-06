from config import Config
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logger import log_it
import smtplib, inspect

def send_email(msg):
    email_stats_time = Config.EMAIL_STATS_TIME
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT
    use_ssl = Config.EMAIL_USE_SSL
    use_tls = Config.EMAIL_USE_TLS
    smtp_user = Config.SMTP_USER
    smtp_password = Config.SMTP_PASSWORD
    email_recipients = Config.EMAIL_RECIPIENTS
    email_subject = Config.EMAIL_SUBJECT

    missing_configs = []

    if not email_stats_time:
        missing_configs.append("EMAIL_STATS_TIME")
    if not smtp_user:
        missing_configs.append("SMTP_USER")
    if not smtp_password:
        missing_configs.append("SMTP_PASSWORD")
    if not email_recipients:
        missing_configs.append("EMAIL_RECIPIENTS")

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
        func = inspect.currentframe().f_code.co_name
        log_it("e", f"Error in {func}: {e}")
        log_it("e", f"Error sending email: {e}")