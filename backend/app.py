from fastapi import FastAPI, Request
from dotenv import load_dotenv
from webhook import set_webhook
from sender_adapter import send_message
import os
import json
load_dotenv()

app = FastAPI(
    title="Telegram CORP AI Integration API",
)

@app.get('/')
def index():
    return "OK"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

set_webhook(TELEGRAM_TOKEN, WEBHOOK_URL)

@app.post('/webhook')
async def handle_webhook(request: Request):
    update = await request.json()

    #TODO ONLY FOR DEVELOPMENT
    # with open('message.json', 'w', encoding='utf-8') as f:
    #     json.dump(update, f, ensure_ascii=False, indent=2)

    message = update['message']

    send_message(message['chat']['id'], "HELLO")

    return 200

    