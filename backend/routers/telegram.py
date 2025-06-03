from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from constants.request_models import BotRegisterRequest
from config.settings import WEBHOOK_URL, INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN
import services.webhook_server as webhook_server
import services.db as db
from datetime import datetime
from pytz import timezone
import httpx

router = APIRouter(tags=["Telegram"])


@router.post('/bot', description="Registers a new bot in the system by saving its credentials and setting up webhook integration")
async def register_bot_by_token(request: BotRegisterRequest):
    token = request.telegram_token.get_secret_value()

    try:
        bot_id = await webhook_server.get_bot_id(token)
    except:
        return HTTPException(status_code=404, detail="Invalid Telegram Bot TOKEN")

    db.create_new_bot(bot_id, token)

    response = await webhook_server.set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

    return response


@router.delete("/bot/{bot_id}", description="Deletes the webhook and credentials for the bot using either the bot ID or token or both")
async def unregister_bot(bot_id: int):
    token = db.get_bot_token(bot_id)
    response = await webhook_server.delete_webhook(token)

    if response["status_code"] == 200:
        db.delete_bot(bot_id)
        return {"detail": f"Bot {bot_id} unregistered successfully"}
    else:
        return response['body']


@router.post('/webhook/{bot_id}', description="Handles webhook calls from telegram", tags=["Telegram"])
async def handle_webhook(bot_id:int, request: Request):
    try:
        update = await request.json()

        #NOTE ONLY FOR DEVELOPMENT
        # with open('message.json', 'w', encoding='utf-8') as f:
        #     import json
        #     json.dump(update, f, ensure_ascii=False, indent=2)

        token = db.get_bot_token(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")
        
        message = update.get("message") or update.get("edited_message")
        if not message:
            raise HTTPException(status_code=400, detail="Unsupported update type")

        from_user = message.get("from", {})
        chat = message.get("chat", {})

        ts = datetime.fromtimestamp(message["date"], tz=timezone("UTC")).isoformat()

        request_body = {
            "eventType": "telegram_message",
            "timestamp": ts,
            "chat": str(chat.get("id")),
            "participant": from_user.get("username") or str(from_user.get("id")),
            "message": {
                "externalId": str(message["message_id"]),
                "text": message.get("text", ""),
                "attachments": [],
                "geoLocation": {
                    "lat": 0,
                    "long": 0
                },
                "date": ts,
                "extraData": {
                    "from": {
                        "id": from_user.get("id"),
                        "username": from_user.get("username"),
                        "language_code": from_user.get("language_code")
                    }
                }
            },
            "externalItem": {
                "externalId": str(message["message_id"]),
                "url": f"https://t.me/{chat.get('username') or 'c'}/{message['message_id']}",
                "title": "Telegram Message",
                "extraData": {
                    "messageType": "text"
                }
            },
            "flags": {
                "newTicketOpened": False,
                "newChatCreated": False,
                "externalPostComment": False
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
                "type": "Audio",
                "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
                "mime": "audio/ogg"
            })
            request_body["externalItem"]["extraData"]["messageType"] = "voice"


        headers = {
            "Authorization": f"Bearer {INTEGRATION_TOKEN}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{INTEGRATION_URL}/{INTEGRATION_CODE}/{bot_id}", json=request_body, headers=headers)

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