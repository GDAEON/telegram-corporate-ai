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


# @router.post('/bot', description="Registers a new bot in the system by saving its credentials and setting up webhook integration")
# async def register_bot_by_token(request: BotRegisterRequest):
#     token = request.telegram_token.get_secret_value()

#     try:
#         bot_id = await webhook_server.get_bot_id(token)
#     except:
#         return HTTPException(status_code=404, detail="Invalid Telegram Bot TOKEN")

#     db.create_new_bot(bot_id, token)

#     response = await webhook_server.set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

#     return response


# @router.delete("/bot/{bot_id}", description="Deletes the webhook and credentials for the bot using either the bot ID or token or both")
# async def unregister_bot(bot_id: int):
#     token = db.get_bot_token(bot_id)
#     response = await webhook_server.delete_webhook(token)

#     if response["status_code"] == 200:
#         db.delete_bot(bot_id)
#         return {"detail": f"Bot {bot_id} unregistered successfully"}
#     else:
#         return response['body']


@router.post('/webhook/{bot_id}', description="Handles webhook calls from telegram", tags=["Telegram"])
async def handle_webhook(bot_id:int, request: Request):
    try:
        update = await request.json()

        #NOTE ONLY FOR DEVELOPMENT
        with open('message.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(update, f, ensure_ascii=False, indent=2)

        # return

        token = db.get_bot_token(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")
        
        message = update.get("message") or update.get("edited_message")
        if not message:
            raise HTTPException(status_code=400, detail="Unsupported update type")

        contact_id = message.get("from", {}).get("id")
        text = message.get("text", "")

        contact_info = message.get("contact")

        if contact_info and not db.bot_has_user(bot_id, contact_id) and db.get_is_bot_owner(bot_id, contact_id):
            db.update_user(bot_id, contact_id, contact_info.get("first_name"), contact_info.get("last_name"), contact_info.get("phone_number"))
            db.bot_set_verified(bot_id, True)

        if text.startswith("/start"):
            _, _, input_uuid = text.partition(" ")
            if db.compare_bot_auth_owner(bot_id, input_uuid):
                contact_button = [
                    [
                        {"text": "Share my phone", "request_contact": True}
                    ]
                ]
                await sender_adapter.send_message(
                    token,
                    contact_id,
                    "Almost done! Please share your contact by tapping the button below.",
                    reply_keyboard=contact_button
                )
                return


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