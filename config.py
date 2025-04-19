from jinja2 import Environment, PackageLoader, select_autoescape
import DAP

def get_config_value(section, key, default=None, is_numeric=False):
    try:
        if is_numeric:
            try:
                number = int(DAP.configGetItem(section, key))
                return number
            except ValueError:
                from logger import log_it
                log_it("e", f"Invalid setting for {section}.{key}. Expected an integer, got {DAP.configGetItem(section, key)}")
                return default
        return DAP.configGetItem(section, key)
    except Exception:
        return default

class Config:
    PLUGIN_NAME = "Cellframe Masternode WebUI"
    ACCESS_TOKEN = str(get_config_value("webui", "access_token", default=None, is_numeric=False))
    AUTH_BYPASS = get_config_value("webui", "auth_bypass", default=False, is_numeric=False)
    AUTO_UPDATE = get_config_value("webui", "auto_update", default=False, is_numeric=False)
    CACHE_AGE_LIMIT = get_config_value("webui", "cache_age_limit", default=4, is_numeric=True)
    CACHE_BLOCKS_INTERVAL = int(get_config_value("webui", "cache_blocks_interval", default=30, is_numeric=True))
    CACHE_REWARDS_INTERVAL = int(get_config_value("webui", "cache_rewards_interval", default=30, is_numeric=True))
    DEBUG = get_config_value("webui", "debug", default=False, is_numeric=False)
    DOWNLOAD_PRERELEASES = get_config_value("webui", "download_prereleases", default=False)
    EMAIL_RECIPIENTS = get_config_value("webui", "email_recipients", default=None, is_numeric=False)
    EMAIL_STATS_ENABLED = get_config_value("webui", "email_stats", default=False, is_numeric=False)
    EMAIL_STATS_TIME = get_config_value("webui", "email_time", default="23:00", is_numeric=False)
    EMAIL_SUBJECT = get_config_value("webui", "email_subject", default=f"{PLUGIN_NAME}", is_numeric=False)
    EMAIL_USE_SSL = get_config_value("webui", "email_use_ssl", default=False, is_numeric=False)
    EMAIL_USE_TLS = get_config_value("webui", "email_use_tls", default=False, is_numeric=False)
    HEARTBEAT_BLOCK_AGE = get_config_value("webui", "heartbeat_block_age", default=12, is_numeric=True)
    HEARTBEAT_NOTIFICATION_AMOUNT = int(get_config_value("webui", "heartbeat_notification_amount", default=5, is_numeric=True))
    NODE_ALIAS = get_config_value("webui", "node_alias", default="CFNode", is_numeric=False)
    PASSWORD = str(get_config_value("webui", "password", default="webui", is_numeric=False))
    PLUGIN_URL = get_config_value("webui", "uri", default=None, is_numeric=False)

    if not PLUGIN_URL:
        PLUGIN_URL = get_config_value("webui", "url", default="webui", is_numeric=False)

    SCHEDULER_DELAY_ON_STARTUP = get_config_value("webui", "scheduler_delay_on_startup", default=120, is_numeric=True)
    SHOW_ICON = get_config_value("webui", "show_icon", default=False, is_numeric=False)
    SMTP_PASSWORD = get_config_value("webui", "smtp_password", default=None, is_numeric=False)
    SMTP_PORT = int(get_config_value("webui", "smtp_port", default="465", is_numeric=True))
    SMTP_SERVER = get_config_value("webui", "smtp_server", default="smtp.gmail.com", is_numeric=False)
    SMTP_USER = get_config_value("webui", "smtp_user", default=None, is_numeric=False)
    TELEGRAM_API_TOKEN = get_config_value("webui", "telegram_api_key", default=None, is_numeric=False)
    TELEGRAM_BOT_TOKEN = get_config_value("webui", "telegram_bot_key", default=None, is_numeric=False)
    TELEGRAM_CHAT_ID = get_config_value("webui", "telegram_chat_id", default=False, is_numeric=False)
    TELEGRAM_STATS_ENABLED = get_config_value("webui", "telegram_stats", default=False, is_numeric=False)
    TELEGRAM_STATS_TIME = get_config_value("webui", "telegram_stats_time", default="23:00", is_numeric=False)
    TEMPLATE = get_config_value("webui", "template", default="cpunk", is_numeric=False)
    USERNAME = str(get_config_value("webui", "username", default="webui", is_numeric=False))

    def jinja_environment():
        env = Environment(
            loader=PackageLoader("cellframe-masternode-webui"),
            autoescape=select_autoescape()
        )
        env.policies['json.dumps_kwargs'] = {'sort_keys': False}
        env.trim_blocks = True
        env.lstrip_blocks = True
        return env
