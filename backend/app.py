import os

from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Request

from request_models import BotRegisterRequest

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

@app.post('/auth_bot')
async def register_bot_token(request: BotRegisterRequest):
    token = request.telegram_token.get_secret_value()

    try:
        bot_id = await webhook_server.get_bot_id(token)
    except:
        return HTTPException(status_code=404, detail="Invalid Telegram Bot TOKEN")

    BOT_TOKENS[bot_id] = token

    response = await webhook_server.set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

    return response



@app.post('/webhook/{bot_id}', description="Handles webhook calls from telegram")
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