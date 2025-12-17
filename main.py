import logging
import logging.config

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


async def check_dvmn_status(context, chat_id):
    logger.info("Запуск опроса dvmn")

    url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {config.DEVMAN_TOKEN}"}
    params = {}
    timeout = 110

    while True:
        response = requests.get(
            url=url,
            headers=headers,
            params=params,
            timeout=timeout,
        )
        params.clear()
        response.raise_for_status()

        response = response.json()
        print(response["request_query"])
        status = response["status"]
        logger.info("сервер вернул статус %s", status)

        if status == "found":
            await context.bot.send_message(
                chat_id=chat_id, text="Работа проверена!"
            )
            logger.info("Сервер вернул нужные данные")
        else:
            timestamp = int(response["timestamp_to_request"])
            params["timestamp"] = timestamp
            logger.info("Повторный запрос с timestamp: %s", timestamp)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_user.id

    if not chat_id == config.TG_CHAT_ID:
        await update.message.reply_text("Доступ запрещён")
        logger.warning("Пользователю %s доступ запрещен", chat_id)

        return

    logger.warning(
        "Пользователь запустил бота в тг",
    )

    await check_dvmn_status(context, chat_id)


def main():
    logger.info("Начало работы программы")

    token = config.TG_BOT_TOKEN
    if not token:
        logger.critical("Программа не получила тг токен")
        return

    app = Application.builder().token(token).build()
    logger.info("Бот запущен")

    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == "__main__":
    main()
