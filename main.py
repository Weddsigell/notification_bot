import requests
from telegram.ext import Application, CommandHandler

import config


async def check_dvmn_status(update, context):
    url = "https://dvmn.org/api/long_polling/"
    headers = {"Authorization": f"Token {dvmn_token}"}
    params = {}
    timeout = 120

    while True:
        response = requests.get(url=url, headers=headers, params=params, timeout=timeout)
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


def main():
    token = config.TG_BOT_TOKEN

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", check_dvmn_status))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
