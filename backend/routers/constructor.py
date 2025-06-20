from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from constants.request_models import SendTextMessageRequest, SendMediaMessageRequest
from config.settings import SCHEME
import services.sender_adapter as sender_adapter
import services.db as db

router = APIRouter(tags=["Constructor"])


@router.get("/schema", description="Return integration JSON schema")
async def get_schema():
    """Return the constructor schema used by the admin panel."""
    return JSONResponse(content=SCHEME)

@router.get("/messengers", description="List all available messenger contacts")
async def list_messengers():
    """Return all users grouped as messenger contacts."""
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

        return {"items": items}
    except Exception as e:
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=500,
        )

@router.get("/{id}/status", description="Return integration status for bot")
async def get_status(id: int):
    """Return status information for the bot."""
    return {
    "status": "active",
    "paymentStatus": "trial",
    "expiresAt": "2022-04-11T07:32:43.329+00:00"
    }


@router.post('/sendTextMessage', description="Send a text message to a chat")
async def send_message(request: SendTextMessageRequest):
    """Send text with optional buttons and quick replies."""
    try:
        token = db.get_bot_token(request.chat.messengerId)
        chat_id = request.chat.contact
        text = request.text
        inline_buttons = request.inlineButtons
        quick_replies = request.quickReplies

        reply_keyboard = None
        if quick_replies:
            reply_keyboard = [
                [
                    {
                        **{"text": qr.text},
                        **({"request_contact": True} if qr.type.lower() == "phone" else {}),
                        **({"request_location": True} if qr.type.lower() in {"geolocation", "location"} else {}),
                    }
                    for qr in row
                ]
                for row in quick_replies
            ]

        response = await sender_adapter.send_message(
            token,
            chat_id,
            text,
            inline_buttons=inline_buttons,
            reply_keyboard=reply_keyboard,
            remove_keyboard=not inline_buttons and not quick_replies,
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


@router.post('/sendMediaMessage', description="Send a media message to a chat")
async def send_media_message(request: SendMediaMessageRequest):
    """Send files such as images or audio with optional caption."""
    try:
        token = db.get_bot_token(request.chat.messengerId)
        chat_id = request.chat.contact
        file_type = request.file.type
        file_url = request.file.url
        file_mime = request.file.mime
        caption = request.caption
        inline_buttons = request.inlineButtons
        quick_replies = request.quickReplies

        reply_keyboard = None
        if quick_replies:
            reply_keyboard = [
                [
                    {
                        **{"text": qr.text},
                        **({"request_contact": True} if qr.type.lower() == "phone" else {}),
                        **({"request_location": True} if qr.type.lower() in {"geolocation", "location"} else {}),
                    }
                    for qr in row
                ]
                for row in quick_replies
            ]

        response = await sender_adapter.send_media(
            token,
            chat_id,
            file_type,
            file_url,
            file_mime,
            caption,
            inline_buttons=inline_buttons,
            reply_keyboard=reply_keyboard,
            remove_keyboard=not inline_buttons and not quick_replies,
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