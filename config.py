from utils import getConfigValue

class Config:
    PLUGIN_NAME = "Cellframe system & node info by Mika H (@CELLgainz)"
    API_TOKEN = getConfigValue("webui", "api_token", default=False)
    AUTH_BYPASS = getConfigValue("webui", "auth_bypass", default=False)
    CACHE_BLOCKS_INTERVAL = getConfigValue("webui", "cache_blocks_interval", default=15)
    CACHE_REWARDS_INTERVAL = getConfigValue("webui", "cache_rewards_interval", default=15)
    DEBUG = getConfigValue("webui", "debug", default=False)
    EMAIL_RECIPIENTS = getConfigValue("webui", "email_recipients", default=None)
    EMAIL_STATS_ENABLED = getConfigValue("webui", "email_stats", default=False)
    EMAIL_STATS_TIME = getConfigValue("webui", "email_time")
    EMAIL_SUBJECT = getConfigValue("webui", "email_subject", default=f"{PLUGIN_NAME}")
    GMAIL_APP_PASSWORD = getConfigValue("webui", "gmail_app_password", default=None)
    GMAIL_USER = getConfigValue("webui", "gmail_user", default=None)
    PASSWORD = getConfigValue("webui", "password", default=False)
    PLUGIN_URI = getConfigValue("webui", "uri", default="webui")
    RATE_LIMIT_ACTIVE = getConfigValue("webui", "rate_limit", default=False)
    TELEGRAM_API_TOKEN = getConfigValue("webui", "telegram_api_key", default=None)
    TELEGRAM_CHAT_ID = getConfigValue("webui", "telegram_chat_id", default=None)
    TELEGRAM_STATS_ENABLED = getConfigValue("webui", "telegram_stats", default=False)
    TELEGRAM_STATS_TIME = getConfigValue("webui", "telegram_stats_time")
    TEMPLATE = getConfigValue("webui", "template", default="cards")
    USERNAME = getConfigValue("webui", "username", default=False)