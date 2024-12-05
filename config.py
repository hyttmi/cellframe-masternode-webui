from jinja2 import Environment, PackageLoader, select_autoescape
import DAP

def get_config_value(section, key, default=None, is_numeric=False):
    try:
        if is_numeric:
            try:
                number = int(DAP.configGetItem(section, key))
                return number
            except ValueError:
                return default
        return DAP.configGetItem(section, key)
    except Exception:
        return default

class Config:
    PLUGIN_NAME = "Cellframe Masternode WebUI"
    API_TOKEN = get_config_value("webui", "api_token", default=False, is_numeric=False)
    AUTH_BYPASS = get_config_value("webui", "auth_bypass", default=False, is_numeric=False)
    CACHE_BLOCKS_INTERVAL = get_config_value("webui", "cache_blocks_interval", default=15, is_numeric=True)
    CACHE_REWARDS_INTERVAL = get_config_value("webui", "cache_rewards_interval", default=15)
    DEBUG = get_config_value("webui", "debug", default=False)
    EMAIL_RECIPIENTS = get_config_value("webui", "email_recipients", default=None)
    EMAIL_STATS_ENABLED = get_config_value("webui", "email_stats", default=False)
    EMAIL_STATS_TIME = get_config_value("webui", "email_time", default=False)
    EMAIL_SUBJECT = get_config_value("webui", "email_subject", default=f"{PLUGIN_NAME}")
    EMAIL_USE_SSL = get_config_value("webui", "email_use_ssl", default=False)
    EMAIL_USE_TLS = get_config_value("webui", "email_use_tls", default=False)
    JSON_EXCLUDE = get_config_value("webui", "json_exclude", default=None)
    PASSWORD = get_config_value("webui", "password", default=False)
    PLUGIN_URI = get_config_value("webui", "uri", default="webui")
    SMTP_PASSWORD = get_config_value("webui", "smtp_password", default=None)
    SMTP_PORT = int(get_config_value("webui", "smtp_port", default="465"))
    SMTP_SERVER = get_config_value("webui", "smtp_server", default="smtp.gmail.com")
    SMTP_USER = get_config_value("webui", "smtp_user", default=None)
    TELEGRAM_API_TOKEN = get_config_value("webui", "telegram_api_key", default=False)
    TELEGRAM_CHAT_ID = get_config_value("webui", "telegram_chat_id", default=False)
    TELEGRAM_STATS_ENABLED = get_config_value("webui", "telegram_stats", default=False)
    TELEGRAM_STATS_TIME = get_config_value("webui", "telegram_stats_time", default=False)
    TEMPLATE = get_config_value("webui", "template", default="cards")
    USERNAME = get_config_value("webui", "username", default=False)
    
    def jinja_environment():
        env = Environment(
            loader=PackageLoader("cellframe-masternode-webui"),
            autoescape=select_autoescape()
        )
        env.policies['json.dumps_kwargs'] = {'sort_keys': False}
        return env
