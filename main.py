import asyncio

import aiohttp
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config


async def check_dvmn_status(context, chat_id):
    try:
        dvmn_token = config.DEVMAN_TOKEN
    except AttributeError:
        raise

    if not dvmn_token or not isinstance(dvmn_token, str):
        raise ValueError("DEVMAN_TOKEN пуст или неверного типа")

    url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {dvmn_token}"}
    params = {}
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(
        headers=headers, timeout=timeout
    ) as session:
        while True:
            try:
                async with session.get(url, params=params) as response:
                    status = response.status

                    if not status == 200:
                        continue

                    try:
                        response_json = await response.json()
                    except Exception:
                        continue
                    finally:
                        pass

                dvmn_status = response_json["status"]

                if dvmn_status == "found":
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

                    timestamp = response_json["last_attempt_timestamp"]
                    params["timestamp"] = timestamp

                timestamp = response_json.get("timestamp_to_request")
                if timestamp is not None:
                    params["timestamp"] = timestamp
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(10)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_user.id

    if context.chat_data.get("bot_task"):
        await update.message.reply_text("Бот уже во всю работает!")
        return

    try:
        user_id = config.TG_CHAT_ID
    except AttributeError:
        raise

    if not user_id or not isinstance(user_id, int):
        raise ValueError("TG_CHAT_ID пуст или неверного типа")

    if not chat_id == user_id:
        await update.message.reply_text("Доступ запрещён")
        return

    task = asyncio.create_task(check_dvmn_status(context, chat_id))
    context.chat_data["bot_task"] = task


async def on_shutdown(app: Application) -> None:
    for chat_id, chat_data in app.chat_data.items():
        task = chat_data.get("bot_task")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                raise


def main() -> None:
    try:
        token = config.TG_BOT_TOKEN
    except AttributeError:
        raise

    if not token or not isinstance(token, str):
        raise ValueError("TG_BOT_TOKEN пуст или неверного типа")

    try:
        app = (
            Application.builder()
            .token(token)
            .post_shutdown(on_shutdown)
            .build()
        )
    except ValueError:
        raise
    except telegram.error.InvalidToken:
        raise
    except Exception:
        raise

    app.add_handler(CommandHandler("start", start))

    try:
        app.run_polling(drop_pending_updates=True)
    except telegram.error.NetworkError:
        raise
    except Exception:
        raise
    finally:
        raise


if __name__ == "__main__":
    main()
