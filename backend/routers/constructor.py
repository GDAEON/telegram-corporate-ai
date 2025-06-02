from fastapi import APIRouter
from fastapi.responses import JSONResponse
from constants.request_models import SendTextMessageRequest, SendMediaMessageRequest
from config.settings import BOT_TOKENS, SCHEME
import services.sender_adapter as sender_adapter

router = APIRouter(tags=["Constructor"])


@router.get("/schema")
def get_schema():
    return JSONResponse(content=SCHEME)


@router.post('/{id}/sendTextMessage', description="Sends message to a bot_{id} chat")
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


@router.post('/{id}/sendMediaMessage', description="Sends media message to a bot_{id} chat")
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