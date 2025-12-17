import asyncio
import logging
import logging.config

import aiohttp
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


async def check_dvmn_status(context, chat_id):
    logger.info("Запуск long polling для dvmn")

    try:
        dvmn_token = config.DEVMAN_TOKEN
    except AttributeError as e:
        logger.critical("DEVMAN_TOKEN не найден в config: %s", e)
        raise

    if not dvmn_token or not isinstance(dvmn_token, str):
        logger.critical("DEVMAN_TOKEN пуст или неверного типа")
        raise ValueError("DEVMAN_TOKEN пуст или неверного типа")

    logger.debug(
        "DEVMAN_TOKEN получен, его длинна %s символов", len(dvmn_token)
    )

    url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {dvmn_token}"}
    params = {}
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(
        headers=headers, timeout=timeout
    ) as session:
        logger.debug(
            "Запуск сессии с параметрами headers: %s, timeout: %s",
            headers,
            timeout,
        )

        while True:
            logger.debug(
                "Get запрос с параметрами url: %s, params: %s", url, params
            )
            try:
                async with session.get(url, params=params) as response:
                    status = response.status
                    raw_text = await response.text()

                    if not status == 200:
                        logger.error(
                            "Получен ответ. Код: %s\nТекст: %s",
                            status,
                            raw_text,
                        )
                        continue

                    try:
                        response_json = await response.json()
                    except Exception as e:
                        logger.error(
                            "Не удалось распарсить ответ в json: %s", e
                        )
                        continue
                    finally:
                        logger.debug(
                            "Получен ответ. Код: %s\nТекст: %s",
                            status,
                            raw_text,
                        )

                dvmn_status = response_json["status"]

                if dvmn_status == "found":
                    logger.info("Получен ответ от dvmn")

                    new_attempts = response_json["new_attempts"]

                    for attempt in new_attempts:
                        name_lesson = attempt["lesson_title"]
                        lesson_url = attempt["lesson_url"]
                        text = f"Работа <{name_lesson}> по ссылке <{lesson_url}> проверена!\n"

                        if attempt["is_negative"]:
                            text += "К сожалению есть ошибки, нужно исправить!"
                        else:
                            text += "Ты большой молодец, ошибок нет!"

                        await context.bot.send_message(
                            chat_id=chat_id, text=text
                        )
                        logger.info("Пользователь получил уведомление")

                    timestamp = response_json["last_attempt_timestamp"]
                    params["timestamp"] = timestamp
                    logger.debug(
                        "Временная метка изменилась на last_attempt_timestamp %s",
                        timestamp,
                    )

                timestamp = response_json.get("timestamp_to_request")
                if timestamp is not None:
                    params["timestamp"] = timestamp
                    logger.debug(
                        "Временная метка изменилась на timestamp_to_request: %s",
                        timestamp,
                    )
            except asyncio.CancelledError:
                logger.warning("остановка long polling для dvmn")
                raise
            except Exception as e:
                logger.error(
                    "Ошибка в long polling: %s Повтор через 10 секунд", e
                )
                await asyncio.sleep(10)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_user.id
    logger.debug("Бот получил обновление от пользователя %s", chat_id)

    if context.chat_data.get("bot_task"):
        await update.message.reply_text("Бот уже во всю работает!")
        return

    try:
        user_id = config.TG_CHAT_ID
    except AttributeError as e:
        logger.critical("TG_CHAT_ID не найден в config: %s", e)
        raise

    if not user_id or not isinstance(user_id, int):
        logger.critical("TG_CHAT_ID пуст или неверного типа")
        raise ValueError("TG_CHAT_ID пуст или неверного типа")

    logger.debug("TG_CHAT_ID получен - %s", user_id)

    if not chat_id == user_id:
        await update.message.reply_text("Доступ запрещён")
        logger.warning("Пользователю %s доступ запрещен", chat_id)

        return

    logger.warning(
        "Пользователь %s запустил бота в тг",
        chat_id,
    )

    task = asyncio.create_task(check_dvmn_status(context, chat_id))
    context.chat_data["bot_task"] = task
    logger.debug("Создана задача")


async def on_shutdown(app: Application) -> None:
    logger.info("Бот останавливается")

    for chat_id, chat_data in app.chat_data.items():
        task = chat_data.get("bot_task")
        if task:
            logger.info("Отмена задачи long polling для chat_id=%s", chat_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Бот остановлен! вручную!")


def main() -> None:
    logger.info("Запуск программы notification_bot")

    try:
        token = config.TG_BOT_TOKEN
    except AttributeError as e:
        logger.critical("TG_BOT_TOKEN не найден в config: %s", e)
        raise

    if not token or not isinstance(token, str):
        logger.critical("TG_BOT_TOKEN пуст или неверного типа")
        raise ValueError("TG_BOT_TOKEN пуст или неверного типа")

    logger.debug("TG_BOT_TOKEN получен, его длинна %s символов", len(token))

    try:
        app = (
            Application.builder()
            .token(token)
            .post_shutdown(on_shutdown)
            .build()
        )
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
        logger.info("Бот, программа завершили работу")


if __name__ == "__main__":
    main()
