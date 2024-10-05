from utils import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sendMail(msg):
    gmail_user = getConfigValue("webui", "gmail_user", None)
    gmail_app_password = getConfigValue("webui", "gmail_app_password", None)
    email_recipients = getConfigValue("webui", "email_recipients", None)
    email_subject = getConfigValue("webui", "email_subject", f"{PLUGIN_NAME}")
    
    missing_configs = []

    if gmail_user is None:
        missing_configs.append("gmail_user")
    if gmail_app_password is None:
        missing_configs.append("gmail_app_password")
    if email_recipients is None:
        missing_configs.append("email_recipients")

    if missing_configs:
        for config in missing_configs:
            logError(f"{config} is not set!")
        return

    email_msg = MIMEMultipart("alternative")
    email_msg["From"] = gmail_user
    email_msg["To"] = ', '.join(email_recipients)
    email_msg["Subject"] = email_subject
    
    part = MIMEText(msg, "html")

    email_msg.attach(part)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, email_recipients, email_msg.as_string())
        server.close()
        logNotice("Email sent!")
    except Exception as e:
        logError(f"Error: {e}")