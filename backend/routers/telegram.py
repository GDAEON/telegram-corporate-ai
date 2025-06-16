from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN
import services.db as db
from datetime import datetime
from datetime import datetime, timezone
import httpx

import services.sender_adapter as sender_adapter

router = APIRouter(tags=["Telegram"])

@router.post('/webhook/{bot_id}', description="Handles webhook calls from telegram", tags=["Telegram"])
async def handle_webhook(bot_id: int, request: Request):
    try:
        update = await request.json()
        
        token = db.get_bot_token(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")

        message = update.get("message") or update.get("edited_message")
        if not message:
            raise HTTPException(status_code=400, detail="Unsupported update type")

        contact_id = message["from"]["id"]
        text = message.get("text", "")
        contact_info = message.get("contact")
        user_status = db.get_botuser_status(bot_id, contact_id)

        if contact_info and db.get_is_bot_owner(bot_id, contact_id):
            db.update_user(
                contact_id,
                contact_info.get("first_name"),
                contact_info.get("last_name"),
                contact_info.get("phone_number"),
            )
            db.bot_set_verified(bot_id, True)
            await sender_adapter.send_message(
                token,
                contact_id,
                "Thanks, you’re all set! 🎉"
            )
            return {"status": "ok"}

        if text.startswith("/start"):
            _, _, input_uuid = text.partition(" ")
            if not input_uuid:
                _, _, input_uuid = text.partition("=")
            input_uuid = input_uuid.strip()
            if input_uuid and db.compare_bot_auth_owner(bot_id, input_uuid):
                contact_button = [
                    [{"text": "Share my phone", "request_contact": True}]
                ]
                db.add_owner_user(bot_id, contact_id)
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    "Almost done! Please share your contact by tapping the button below.",
                    reply_keyboard=contact_button
                )
                return {"status": "ok"}
            elif input_uuid and db.compare_bot_auth_pass(bot_id, input_uuid):
                db.add_user_to_a_bot(
                    bot_id,
                    contact_id,
                    message["from"].get("first_name"),
                    message["from"].get("last_name"),
                    None,
                )
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    "You have successfully joined the bot!"
                )
                return {"status": "ok"}
            else:
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    "Sorry, I didn’t recognize that code. Please try again."
                )
                return {"status": "ok"}

        if user_status is None:
            await sender_adapter.send_message(
                token,
                contact_id,
                "Sorry, you are not allowed to use this bot!"
            )
            return {"status": "ok"}
        if user_status is False:
            await sender_adapter.send_message(
                token,
                contact_id,
                "Sorry, seems like your account is deactivated, contact support"
            )
            return {"status": "ok"}


        ts = int(datetime.now(tz=timezone.utc).timestamp())
        date = datetime.now().strftime("%d.%m.%Y")

        request_body = {
            "eventType": "InboxReceived",
            "timestamp": ts,
            "chat": {
                "externalId": "12",
                "messengerInstance": "12",
                "messengerId": f"{bot_id}",
                "contact": {
                    "externalId": f"{contact_id}"
                }
            },
            "participant": "igor",
            "message": {
                "externalId": "146379262",
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
            response = await client.post(f"{INTEGRATION_URL}/{INTEGRATION_CODE}/12/event", json=request_body, headers=headers)

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        if response.content:
            try:
                return response.json()
            except Exception:
                return {"status": "ok", "raw_response": response.text}
        else:
            return {"status": "ok", "message": "No content"}
    
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=400)