from environs import Env

env = Env()
env.read_env()


TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
DEVMAN_TOKEN = env.str("DEVMAN_TOKEN")
TG_CHAT_ID = env.int("TG_CHAT_ID")
