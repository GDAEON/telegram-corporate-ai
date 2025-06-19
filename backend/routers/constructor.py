from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from constants.request_models import SendTextMessageRequest, SendMediaMessageRequest
from config.settings import SCHEME
import services.sender_adapter as sender_adapter
import services.db as db

router = APIRouter(tags=["Constructor"])


@router.get("/schema")
async def get_schema():
    return JSONResponse(content=SCHEME)

@router.get("/messengers")
async def list_messengers():
    try:
        bot_users = db.get_all_bot_users()
        items = [
            {
                "externalType": "telegram",
                "externalId": f"{user_id}",
                "name": f"{name or ''} {surname or ''}".strip(),
                "messengerId": f"12", # TODO replace with bot id
                "internalType": "Telegram",
            }
            for bot_id, user_id, name, surname in bot_users
        ]
        print(items)
        return {"items": items}
    except Exception as e:
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=500,
        )

@router.get("/{id}/status")
async def get_status(id: int):
    return {
    "status": "active",
    "paymentStatus": "trial",
    "expiresAt": "2022-04-11T07:32:43.329+00:00"
    }


@router.post('/sendTextMessage', description="Sends message to a chat")
async def send_message(request: SendTextMessageRequest):
    try:
        print("sendTextMessage request:", request.dict())
        token = db.get_bot_token(request.chat.messengerId)
        chat_id = request.chat.contact
        text = request.text
        inline_buttons = request.inlineButtons

        if inline_buttons:
            print("INLINE BUTTONS RECEIVED")

        response = await sender_adapter.send_message(
            token,
            chat_id,
            text,
            inline_buttons=inline_buttons,
            bot_id=request.chat.messengerId,
        )

        if response["status_code"] == 200:

            messenger_id = request.chat.messengerId
            return {"externalId": chat_id, "messengerId": messenger_id}
        else:
            return JSONResponse(
                content={"message": str(e), "code": "feature_not_supported"},
                status_code=202
            )

        
    except Exception as e:
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=202
        )


@router.post('/sendMediaMessage', description="Sends media message to a chat")
async def send_media_message(request: SendMediaMessageRequest):
    try:
        print("sendMediaMessage request:", request.dict())
        token = db.get_bot_token(request.chat.messengerId)
        chat_id = request.chat.contact
        file_type = request.file.type
        file_url = request.file.url
        file_mime = request.file.mime
        caption = request.caption
        inline_buttons = request.inlineButtons

        if inline_buttons:
            print("INLINE BUTTONS RECEIVED")

        response = await sender_adapter.send_media(
            token,
            chat_id,
            file_type,
            file_url,
            file_mime,
            caption,
            inline_buttons=inline_buttons,
            bot_id=request.chat.messengerId,
        )

        if response["status_code"] == 200:
            messenger_id = request.chat.messengerId
            return {"externalId": chat_id, "messengerId": messenger_id}
        else:
            return {"message": response['body'], "code": "feature_not_supported"}

    except Exception as e:
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=202
        )