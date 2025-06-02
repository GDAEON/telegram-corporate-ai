import os

from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Request, Query

from request_models import BotRegisterRequest, BotUnregisterRequest, SendTextMessageRequest, SendMediaMessageRequest

import sender_adapter
import webhook_server

from dotenv import load_dotenv
load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

#TODO Move to PostgreSQL Database
BOT_TOKENS: dict[int, str] = {}

app = FastAPI(
    title="Telegram CORP AI Integration API",
)

@app.post('/bot', description="Registers a new bot in the system by saving its credentials and setting up webhook integration", tags=["Telegram"])
async def register_bot_by_token(request: BotRegisterRequest):
    token = request.telegram_token.get_secret_value()

    try:
        bot_id = await webhook_server.get_bot_id(token)
    except:
        return HTTPException(status_code=404, detail="Invalid Telegram Bot TOKEN")

    BOT_TOKENS[bot_id] = token
    print(bot_id)

    response = await webhook_server.set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

    return response

@app.delete("/bot", description="Deletes the webhook and credentials for the bot using either the bot ID or token or both", tags=["Telegram"])
async def unregister_bot(
    request: BotUnregisterRequest
):
    token = request.token.get_secret_value() if request.token else None
    bot_id = request.bot_id

    if not token and bot_id is None:
        raise HTTPException(status_code=400, detail="Either bot_id or token must be provided")

    if not token:
        token = BOT_TOKENS.get(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot ID not found")
    
    if bot_id is None:
        matched = [k for k, v in BOT_TOKENS.items() if v == token]
        if not matched:
            raise HTTPException(status_code=404, detail="Token not found")
        bot_id = matched[0]
    
    await webhook_server.delete_webhook(token)

    BOT_TOKENS.pop(bot_id, None)

    return {"detail": f"Bot {bot_id} unregistered successfully"}


@app.post('/webhook/{bot_id}', description="Handles webhook calls from telegram", tags=["Telegram"])
async def handle_webhook(bot_id:int, request: Request):
    try:
        update = await request.json()

        #NOTE ONLY FOR DEVELOPMENT
        # with open('message.json', 'w', encoding='utf-8') as f:
        #     import json
        #     json.dump(update, f, ensure_ascii=False, indent=2)

        token = BOT_TOKENS.get(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")
        

        return {"status": "OK"}
    

    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=400)
    
@app.get("/schema", tags=["Constructor"])
def get_schema():
    return JSONResponse(content={
        "messenger_types": {
            "telegram": {
                "extends": "with_buttons",
                "name": "Telegram",
                "internal_type": "telegram",
                "quick_replies": {
                    "text": True,
                    "text_max_length": 20,
                    "phone": True,
                    "geolocation": True,
                    "max_count": 32
                },
                "inline_buttons": {
                    "text": True,
                    "url": True,
                    "payload": True,
                    "payload_max_length": 64,
                    "text_max_length": 20,
                    "colors": True,
                    "max_count": 32
                },
                "text": {
                    "max_length": 4096
                },
                "image": {
                    "enabled": True,
                    "mime": ["image/jpeg", "image/png"],
                    "max_file_size": 5 * 1024 * 1024,
                    "caption": True,
                    "caption_max_length": 1024
                },
                "video": {
                    "enabled": True,
                    "mime": ["video/mp4"],
                    "max_file_size": 20 * 1024 * 1024,
                    "caption": True,
                    "caption_max_length": 1024
                },
                "document": {
                    "enabled": True,
                    "mime": ["*"],
                    "max_file_size": 20 * 1024 * 1024,
                    "caption": True,
                    "caption_max_length": 1024
                },
                "audio": {
                    "enabled": True,
                    "mime": ["audio/mpeg", "audio/ogg"],
                    "max_file_size": 5 * 1024 * 1024
                },
                "voice": {
                    "enabled": True,
                    "mime": ["audio/ogg"],
                    "max_file_size": 1 * 1024 * 1024
                },
                "geolocation": {
                    "enabled": False
                }
            }
        }
    })

@app.post('/{id}/sendTextMessage', description="Sends message to a bot_{id} chat", tags=["Constructor"])
async def send_message(id: int, request: SendTextMessageRequest):
    try:
        token = BOT_TOKENS.get(id)
        chat_id = request.chat.externalId
        text = request.text

        response = await sender_adapter.send_message(token, chat_id, text)

        if response["status_code"] == 200:

            messenger_id = request.chat.messengerId
            return {"externalId": chat_id, "messengerId": messenger_id}
        else:
            return {"message": response['body'], "code": "feature_not_supported"}
        
    except Exception as e:
        return {"message": e, "code": "feature_not_supported"}

@app.post('/{id}/sendMediaMessage', description="Sends media message to a bot_{id} chat", tags=["Constructor"])
async def send_media_message(id: int, request: SendMediaMessageRequest):
    try:
        token = BOT_TOKENS.get(id)
        chat_id = request.chat.externalId
        file_type = request.file.type
        file_url = request.file.url
        file_mime = request.file.mime
        caption = request.caption

        response  = await sender_adapter.send_media(token, chat_id, file_type, file_url, file_mime, caption)

        if response["status_code"] == 200:
            messenger_id = request.chat.messengerId
            return {"externalId": chat_id, "messengerId": messenger_id}
        else:
            return {"message": response['body'], "code": "feature_not_supported"}
        
    except Exception as e:
        return {"message": e, "code": "feature_not_supported"}