from fastapi import APIRouter
from fastapi.responses import JSONResponse
from constants.request_models import SendTextMessageRequest, SendMediaMessageRequest
from config.settings import SCHEME
import services.sender_adapter as sender_adapter
import services.postgresql_db as pdb

router = APIRouter(tags=["Constructor"])


@router.get("/schema")
async def get_schema():
    return JSONResponse(content=SCHEME)

@router.get("/{id}/status")
async def get_status(id: int):
    return {
    "status": "active",
    "paymentStatus": "trial",
    "expiresAt": "2022-04-11T07:32:43.329+00:00"
    }


@router.post('/{id}/sendTextMessage', description="Sends message to a bot_{id} chat")
async def send_message(id: int, request: SendTextMessageRequest):
    try:
        token = pdb.get_bot_token(id)
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
        token = pdb.get_bot_token(id)
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