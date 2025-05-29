import os

from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Request, Query

from request_models import BotRegisterRequest, BotUnregisterRequest

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

        message = update['message']

        response = await sender_adapter.send_message(token, message['chat']['id'], "HELLO")

        return response
    

    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=400)
    
