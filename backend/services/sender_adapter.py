import httpx
import json
from io import BytesIO
from datetime import datetime
from datetime import datetime, timezone
from services.helper_functions import guess_filename
from typing import List, Optional, Dict, Any
from constants.prometheus_models import MESSAGE_COUNT, MESSAGE_TEXT_COUNT
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN
from services.logging_setup import interaction_logger


async def send_message(
    token: str,
    chat_id: int,
    text: str,
    inline_buttons: Optional[List[List[Dict[str, Any]]]] = None,
    reply_keyboard: Optional[List[List[Dict[str, Any]]]] = None,
    remove_keyboard: bool = False,
    parse_mode: str = "HTML",
    bot_id: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    if bot_id is not None:
        MESSAGE_COUNT.labels(direction="outgoing", bot_id=str(bot_id)).inc()
        MESSAGE_TEXT_COUNT.labels(
            direction="outgoing",
            bot_id=str(bot_id),
            text=text[:100],
        ).inc()
        interaction_logger.info(
            f"OUTGOING bot_id={bot_id} chat_id={chat_id} text={text}"
        )

    if remove_keyboard:
        payload["reply_markup"] = {"remove_keyboard": True}
    elif inline_buttons:
        payload["reply_markup"] = {"inline_keyboard": inline_buttons}
    elif reply_keyboard:
        payload["reply_markup"] = {
            "keyboard": reply_keyboard,
            "resize_keyboard": True,
            "one_time_keyboard": True,
        }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload
        )

    result = {"status_code": resp.status_code, "body": resp.json()}
    if bot_id is not None:
        interaction_logger.info(
            f"SENT bot_id={bot_id} status={resp.status_code} response={result['body']}"
        )
    return result


    
    
async def send_media(
    token: str,
    chat_id: int,
    file_type: str,
    file_url: str,
    file_mime: str,
    caption: str,
    inline_buttons: Optional[List[List[Dict[str, Any]]]] = None,
    reply_keyboard: Optional[List[List[Dict[str, Any]]]] = None,
    remove_keyboard: bool = False,
    bot_id: Optional[int] = None,
):
    if bot_id is not None:
        MESSAGE_COUNT.labels(direction="outgoing", bot_id=str(bot_id)).inc()
        MESSAGE_TEXT_COUNT.labels(
            direction="outgoing",
            bot_id=str(bot_id),
            text=(caption or "")[:100],
        ).inc()
        interaction_logger.info(
            f"OUTGOING_MEDIA bot_id={bot_id} chat_id={chat_id} type={file_type} caption={caption}"
        )
    async with httpx.AsyncClient() as client:
        file_response = await client.get(file_url, follow_redirects=True)
        file_response.raise_for_status()

        content = file_response.content
        file_size = len(content)

        method_map = {
            "Image": ("sendPhoto", "photo", 5 * 1024 * 1024),
            "Video": ("sendVideo", "video", 20 * 1024 * 1024),
            "Document": ("sendDocument", "document", 20 * 1024 * 1024),
            "Audio": ("sendAudio", "audio", 5 * 1024 * 1024),
            "Voice": ("sendVoice", "voice", 1 * 1024 * 1024)
        }

        if file_type not in method_map:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        method, field_name, max_size = method_map[file_type]

        if file_size > max_size:
            raise ValueError(f"{file_type} exceeds max file size of {max_size} bytes")
        
        filename = guess_filename(file_url, file_response.headers)
        
        files = {
            field_name: (filename, BytesIO(content), file_mime)
        }

        data = {
            "chat_id": str(chat_id),
        }
        if caption and file_type in ["image", "video", "document"]:
            data["caption"] = caption[:1024]
        if inline_buttons:
            data["reply_markup"] = json.dumps({"inline_keyboard": inline_buttons})
        elif reply_keyboard:
            data["reply_markup"] = json.dumps({
                "keyboard": reply_keyboard,
                "resize_keyboard": True,
                "one_time_keyboard": True,
            })
        elif remove_keyboard:
            data["reply_markup"] = json.dumps({"remove_keyboard": True})

        response = await client.post(
            f"https://api.telegram.org/bot{token}/{method}",
            data=data,
            files=files
        )

        result = {
            "status_code": response.status_code,
            "body": response.json()
        }
        if bot_id is not None:
            interaction_logger.info(
                f"SENT_MEDIA bot_id={bot_id} status={response.status_code} response={result['body']}"
            )
        return result


def _build_event_request(message_id: int, text: str, contact_id: int, messengerId: int, participant_name: str):
    ts = int(datetime.now(tz=timezone.utc).timestamp())
    date = datetime.now().strftime("%d.%m.%Y")

    return {
        "eventType": "InboxReceived",
        "timestamp": ts,
        "chat": {
            "externalId": f"{contact_id}",
            "messengerInstance": f"{contact_id}",
            "messengerId": f"{messengerId}",
            "contact": {"externalId": f"{contact_id}"},
        },
        "participant": participant_name,
        "message": {
            "externalId": f"{message_id}",
            "text": f"{text}",
            "date": f"{date}",
            "attachments": [],
        },
        "externalItem": {"extraData": {}},
    }

async def _forward_message(request_body: dict):
    headers = {
        "Authorization": f"Bearer {INTEGRATION_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        return await client.post(
            f"{INTEGRATION_URL}/{INTEGRATION_CODE}/12/event",
            json=request_body,
            headers=headers,
        )