from environs import Env

env = Env()
env.read_env()


TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
DEVMAN_TOKEN = env.str("DEVMAN_TOKEN")
TG_CHAT_ID = env.str("TG_CHAT_ID")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(name)s | %(process)d | %(lineno)d | %(filename)s "
            "%(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "logfile": {
            "formatter": "default",
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "notification_bot.log",
            "encoding": "utf-8",
            "mode": "w",
        },
    },
    "loggers": {"__main__": {"level": "DEBUG", "handlers": ["logfile"]}},
}