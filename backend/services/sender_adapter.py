import httpx
from io import BytesIO
from services.helper_functions import guess_filename
from typing import List, Optional, Dict, Any


async def send_message(
    token: str,
    chat_id: int,
    text: str,
    inline_buttons: Optional[List[List[Dict[str, Any]]]] = None,
    reply_keyboard: Optional[List[List[Dict[str, Any]]]] = None,
    parse_mode: str = "HTML",
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    if inline_buttons:
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
    return {"status_code": resp.status_code, "body": resp.json()}


    
    
async def send_media(token: str, chat_id: int, file_type: str, file_url: str, file_mime: str, caption: str):
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

        response = await client.post(
            f"https://api.telegram.org/bot{token}/{method}",
            data=data,
            files=files
        )

        return {
            "status_code": response.status_code,
            "body": response.json()
        }
