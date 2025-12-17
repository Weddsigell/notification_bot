import logging
import logging.config

import requests
import telegram
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

async def on_shutdown(app: Application) -> None:
    logger.info("Бот остановлен пользователем")


def main() -> None:
    logger.info("Запуск программы notification_bot")

    try:
        token = config.TG_BOT_TOKEN
    except AttributeError as e:
        logger.critical("Токен бота не найден в config: %s", e)
        raise

    if not token or not isinstance(token, str):
        logger.critical(
            "Токен бота пуст или неверного типа: %s"
        )
        raise ValueError("Токен бота пуст или неверного типа")

    logger.debug(
        "Токен бота получен, его длинна %s символов", len(token)
    )

    try:
        app = Application.builder().token(token).post_shutdown(on_shutdown).build()
        logger.info("Бот создан")
    except ValueError as e:
        logger.critical("Неверный или пустой токен бота: %s", e)
        raise
    except telegram.error.InvalidToken as e:
        logger.critical("Токен бота недействителен: %s", e)
        raise
    except Exception as e:
        logger.critical(
            "Неожиданная ошибка при создании бота: %s", e, exc_info=True
        )
        raise

    app.add_handler(CommandHandler("start", start))

    try:
        logger.info("Бот начинает работу")
        app.run_polling(drop_pending_updates=True)
    except telegram.error.NetworkError as e:
        logger.error("Сетевая ошибка Telegram: %s", e)
    except Exception as e:
        logger.critical("Неожиданная ошибка бота: %s", e, exc_info=True)
        raise
    finally:
        logger.info("Бот завершил работу")


if __name__ == "__main__":
    main()
