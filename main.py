import logging
import logging.config

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


async def check_dvmn_status():
    logger.info("Запуск опроса dvmn")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != config.TG_CHAT_ID:
        await update.message.reply_text("Доступ запрещён")
        return

    await check_dvmn_status()


def main():
    logger.info("Начало работы программы")

    token = config.TG_BOT_TOKEN
    if not token:
        logger.critical("Программа не получила тг токен")
        return

    app = ApplicationBuilder.token(token).build()
    logger.info("Бот запущен")

    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == "__main__":
    main()
