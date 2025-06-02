from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from constants.request_models import BotRegisterRequest
from config.settings import WEBHOOK_URL
import services.webhook_server as webhook_server
import services.postgresql_db as pdb

router = APIRouter(tags=["Telegram"])


@router.post('/bot', description="Registers a new bot in the system by saving its credentials and setting up webhook integration")
async def register_bot_by_token(request: BotRegisterRequest):
    token = request.telegram_token.get_secret_value()

    try:
        bot_id = await webhook_server.get_bot_id(token)
    except:
        return HTTPException(status_code=404, detail="Invalid Telegram Bot TOKEN")

    pdb.create_new_bot(bot_id, token)

    response = await webhook_server.set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

    return response


@router.delete("/bot/{bot_id}", description="Deletes the webhook and credentials for the bot using either the bot ID or token or both")
async def unregister_bot(bot_id: int):
    token = pdb.get_bot_token(bot_id)
    response = await webhook_server.delete_webhook(token)

    if response["status_code"] == 200:
        pdb.delete_bot(bot_id)
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

        token = pdb.get_bot_token(bot_id)
        if not token:
            raise HTTPException(status_code=404, detail="Bot not registered")
        

        return {"status": "OK"}
    
    except Exception as e:
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=400)