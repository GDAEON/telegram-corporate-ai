from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from constants.request_models import SendTextMessageRequest, SendMediaMessageRequest, SendSystemMessageRequest
from config.settings import SCHEME
import services.sender_adapter as sa
import services.db as db
from services.logging_setup import interaction_logger
import constants.redis_models as rdb
import services.helper_functions as hf
import json
import asyncio

router = APIRouter(tags=["Constructor"])


@router.get("/schema", description="Return integration JSON schema")
async def get_schema():
    """Return the constructor schema used by the admin panel."""
    return JSONResponse(content=SCHEME)

@router.get("/{id}/messengers", description="List all available messenger contacts")
async def list_messengers():
    """Return all users grouped as messenger contacts."""
    try:
        bot_users = db.get_all_bot_users()
        items = [
            {
                "externalType": "employees",
                "externalId": f"{user_id}",
                "name": f"{name or ''} {surname or ''}".strip(),
                # "messengerId": f"{user_id}",
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


@router.post('/{id}/sendTextMessage', description="Send a text message to a chat")
async def send_message(id: int, request: SendTextMessageRequest):
    """Send text with optional buttons and quick replies."""
    try:
        messenger_id = id
        #TODO Remove 
        if int(id) == 12:
            messenger_id = '7922062448'
        interaction_logger.info(
            f"Sending text message to {request.chat.contact} via bot {messenger_id}"
        )
        token = db.get_bot_token(messenger_id)
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

        response = await sa.send_message(
            token,
            chat_id,
            text,
            inline_buttons=inline_buttons,
            reply_keyboard=reply_keyboard,
            remove_keyboard=not inline_buttons and not quick_replies,
            bot_id=messenger_id,
        )

        if response["status_code"] == 200:
            interaction_logger.info(
                f"Text message sent to {chat_id} via bot {messenger_id}"
            )
            return {"externalId": chat_id, "messengerId": chat_id}
        else:
            interaction_logger.error(
                f"Failed to send text message via bot {messenger_id}: {response['body']}"
            )
            return JSONResponse(
                content={"message": f"Failed to send text message via bot {messenger_id}: {response['body']}",
                          "code": "feature_not_supported"},
                status_code=202
            )

        
    except Exception as e:
        interaction_logger.error(f"Text send failed: {e}")
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=202
        )


@router.post('/{id}/sendMediaMessage', description="Send a media message to a chat")
async def send_media_message(id: int, request: SendMediaMessageRequest):
    """Send files such as images or audio with optional caption."""
    try:
        messenger_id = id
        #TODO Remove 
        if int(id) == 12:
            messenger_id = '7922062448'
        interaction_logger.info(
            f"Sending media message to {request.chat.contact} via bot {messenger_id}"
        )
        token = db.get_bot_token(messenger_id)
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

        response = await sa.send_media(
            token,
            chat_id,
            file_type,
            file_url,
            file_mime,
            caption,
            inline_buttons=inline_buttons,
            reply_keyboard=reply_keyboard,
            remove_keyboard=not inline_buttons and not quick_replies,
            bot_id=messenger_id,
        )

        if response["status_code"] == 200:
            interaction_logger.info(
                f"Media message sent to {chat_id} via bot {messenger_id}"
            )
            return {"externalId": chat_id, "messengerId": chat_id}
        else:
            interaction_logger.error(
                f"Failed to send media via bot {messenger_id}: {response['body']}"
            )
            return {"message": response['body'], "code": "feature_not_supported"}

    except Exception as e:
        interaction_logger.error(f"Media send failed: {e}")
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=202
        )
    

@router.post('/{id}/sendSystemMessage', description="Send a message message")
async def send_system_message(id: int, request: SendSystemMessageRequest):
    try:
        messenger_id = id
        #TODO Remove 
        if int(id) == 12:
            messenger_id = '7922062448'
        interaction_logger.info(
            f"Receiving system message from {request.chat.contact} from bot {messenger_id}"
        )
        chat_id = request.chat.contact
        
        text = request.text

        interaction_logger.info(text) 

        project_data = json.loads(text)

        event = project_data.get("event")

        if event == "started":
            message_id = project_data.get("req_id")
            if message_id:
                cached = rdb.Message.get(messenger_id, chat_id, message_id)
                if cached:
                    text, participant, attachments, message_type = cached
                    request_body = sa._build_event_request(
                        message_id,
                        text,
                        chat_id,
                        messenger_id,
                        participant,
                        attachments,
                        message_type,
                    )
                    asyncio.create_task(sa._forward_message(request_body))
                rdb.Message.delete(messenger_id, chat_id, message_id)

            session_id = project_data.get("session_id")
            if session_id:
                selected_project_id = db.get_selected_project_id(messenger_id, chat_id)
                if selected_project_id:
                    rdb.Session.set(messenger_id, chat_id, session_id, selected_project_id)
        
        elif event == "stopped":
            session_id = project_data.get("session_id")

            if session_id:
                project_id = rdb.Session.get(messenger_id, chat_id, session_id)

                db.deselect_project(project_id, messenger_id, chat_id)

                rdb.Session.delete(messenger_id, chat_id, session_id)
        

        return {"externalId": chat_id, "messengerId": chat_id}

    except Exception as e:
        interaction_logger.error(f"System message failed: {e}")
        return JSONResponse(
            content={"message": str(e), "code": "internal_server_error"},
            status_code=202
        )