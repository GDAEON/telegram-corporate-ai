from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN
import services.db as db
from datetime import datetime
from datetime import datetime, timezone
import httpx

import services.sender_adapter as sender_adapter
from services.logging_setup import interaction_logger
from constants.prometheus_models import MESSAGE_COUNT, MESSAGE_TEXT_COUNT

router = APIRouter(tags=["Telegram"])

MESSAGES = {
    "all_set": {
        "en": "Thanks, you’re all set! 🎉",
        "ru": "Спасибо, все готово! 🎉",
    },
    "bot_has_owner": {
        "en": "Sorry, this bot already has an owner.",
        "ru": "Извините, у этого бота уже есть владелец.",
    },
    "logged_in": {"en": "You are logged in!", "ru": "Вы вошли!"},
    "share_contact": {
        "en": "Almost done! Please share your contact by tapping the button below.",
        "ru": "Почти готово! Пожалуйста, поделитесь своим контактом, нажав кнопку ниже.",
    },
    "share_phone_btn": {"en": "Share my phone", "ru": "Поделиться телефоном"},
    "bad_code": {
        "en": "Sorry, I didn’t recognize that code. Please try again.",
        "ru": "Извините, я не распознал этот код. Попробуйте ещё раз.",
    },
    "not_allowed": {
        "en": "Sorry, you are not allowed to use this bot!",
        "ru": "Извините, вы не можете использовать этого бота!",
    },
    "deactivated": {
        "en": "Sorry, seems like your account is deactivated, contact support",
        "ru": "Извините, ваша учетная запись отключена, обратитесь в поддержку",
    },
}

def tr(key: str, locale: str) -> str:
    return MESSAGES.get(key, {}).get(locale, MESSAGES[key]["en"])

@router.post('/webhook/{bot_id}', description="Handles webhook calls from telegram", tags=["Telegram"])
async def handle_webhook(bot_id: int, request: Request):
    try:
        update = await request.json()

        token = db.get_bot_token(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")

        locale = db.get_bot_locale(bot_id) or "en"

        message = update.get("message") or update.get("edited_message")
        if not message:
            print("Exception: Unsupported update type")
            raise HTTPException(status_code=400, detail="Unsupported update type")

        contact_id = message["from"]["id"]
        text = message.get("text", "")
        MESSAGE_COUNT.labels(direction="incoming", bot_id=str(bot_id)).inc()
        MESSAGE_TEXT_COUNT.labels(
            direction="incoming",
            bot_id=str(bot_id),
            text=text[:100],
        ).inc()
        interaction_logger.info(
            f"INCOMING bot_id={bot_id} user_id={contact_id} text={text}"
        )
        contact_info = message.get("contact")
        user_status = db.get_botuser_status(bot_id, contact_id)

        if contact_info and db.bot_has_user(bot_id, contact_id):
            db.update_user(
                contact_id,
                contact_info.get("first_name"),
                contact_info.get("last_name"),
                contact_info.get("phone_number"),
            )
            if db.get_is_bot_owner(bot_id, contact_id):
                db.bot_set_verified(bot_id, True)
            await sender_adapter.send_message(
                token,
                contact_id,
                tr("all_set", locale),
                remove_keyboard=True,
                bot_id=bot_id,
            )
            return {"status": "ok"}

        if text.startswith("/start"):
            _, _, input_uuid = text.partition(" ")
            if not input_uuid:
                _, _, input_uuid = text.partition("=")
            input_uuid = input_uuid.strip()
            if input_uuid and db.compare_bot_auth_owner(bot_id, input_uuid):
                existing_owner = db.get_bot_owner_id(bot_id)
                if existing_owner and existing_owner != contact_id:
                    await sender_adapter.send_message(
                        token,
                        contact_id,
                        tr("bot_has_owner", locale),
                        bot_id=bot_id,
                    )
                    return {"status": "ok"}

                if db.get_is_bot_owner(bot_id, contact_id) and db.owner_has_contact(bot_id, contact_id):
                    db.bot_set_verified(bot_id, True)
                    await sender_adapter.send_message(
                        token,
                        contact_id,
                        tr("logged_in", locale),
                        bot_id=bot_id,
                    )
                    return {"status": "ok"}

                contact_button = [[{"text": tr("share_phone_btn", locale), "request_contact": True}]]
                if not db.get_is_bot_owner(bot_id, contact_id):
                    db.add_owner_user(bot_id, contact_id)
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    tr("share_contact", locale),
                    reply_keyboard=contact_button,
                    bot_id=bot_id,
                )
                return {"status": "ok"}
            elif input_uuid and db.compare_bot_auth_pass(bot_id, input_uuid):
                if db.bot_has_user(bot_id, contact_id):
                    await sender_adapter.send_message(
                        token,
                        contact_id,
                        tr("logged_in", locale),
                    )
                    return {"status": "ok"}

                contact_button = [[{"text": tr("share_phone_btn", locale), "request_contact": True}]]
                db.add_user_to_a_bot(
                    bot_id,
                    contact_id,
                    message["from"].get("first_name"),
                    message["from"].get("last_name"),
                    None,
                )
                db.mark_pass_token_used(bot_id, input_uuid)
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    tr("share_contact", locale),
                    reply_keyboard=contact_button,
                    bot_id=bot_id,
                )
                return {"status": "ok"}
            else:
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    tr("bad_code", locale),
                    bot_id=bot_id,
                )
                return {"status": "ok"}

        if user_status is None:
            await sender_adapter.send_message(
                token,
                contact_id,
                tr("not_allowed", locale),
                bot_id=bot_id,
            )
            return {"status": "ok"}
        if user_status is False:
            await sender_adapter.send_message(
                token,
                contact_id,
                tr("deactivated", locale),
                bot_id=bot_id,
            )
            return {"status": "ok"}


        ts = int(datetime.now(tz=timezone.utc).timestamp())
        date = datetime.now().strftime("%d.%m.%Y")

        user_info = message.get("from", {})
        participant_name = (
            user_info.get("username")
            or " ".join(
                part for part in [user_info.get("first_name"), user_info.get("last_name")] if part
            )
        )

        request_body = {
            "eventType": "InboxReceived",
            "timestamp": ts,
            "chat": {
                "externalId": f"{contact_id}",
                "messengerInstance": "12", # TODO replace with bot_id
                "messengerId": f"{bot_id}",
                "contact": {
                    "externalId": f"{contact_id}"
                }
            },
            "participant": participant_name,
            "message": {
                "externalId": "146379262", # TODO replace with message_id
                "text": f"{text}",
                "date": f"{date}"
            }
        }

        if "photo" in message:
            photo = message["photo"][-1]
            file_id = photo["file_id"]
            request_body["message"]["attachments"].append({
                "type": "Image",
                "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
                "mime": "image/jpeg"
            })
            request_body["externalItem"]["extraData"]["messageType"] = "photo"

        elif "voice" in message:
            file_id = message["voice"]["file_id"]
            request_body["message"]["attachments"].append({
                "type": "Voice",
                "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
                "mime": "audio/ogg"
            })
            request_body["externalItem"]["extraData"]["messageType"] = "voice"


        headers = {
            "Authorization": f"Bearer {INTEGRATION_TOKEN}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{INTEGRATION_URL}/{INTEGRATION_CODE}/12/event", json=request_body, headers=headers) #TODO replace with bot_id

        if response.status_code >= 400:
            print("Exception", response.text)
            raise HTTPException(status_code=response.status_code, detail=response.text)

        if response.content:
            try:
                return response.json()
            except Exception:
                return {"status": "ok", "raw_response": response.text}
        else:
            return {"status": "ok", "message": "No content"}
    
    except Exception as e:
        print("Exception", e)
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=400)