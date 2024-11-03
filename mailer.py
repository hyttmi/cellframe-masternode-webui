from utils import logError, logNotice
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config

def sendMail(msg):
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

    if missing_configs:
        for config in missing_configs:
            logError(f"{config} is not set!")
        return

    if not use_ssl and not use_tls:
        logError("SSL or TLS must be enabled for email sending!")
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
            if use_tls:
                server.starttls()
                server.ehlo()

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, email_recipients, email_msg.as_string())
        server.close()
        logNotice("Email sent!")
    except Exception as e:
        logError(f"Error sending email: {e}")