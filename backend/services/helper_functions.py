from urllib.parse import urlparse
import uuid
import os
import re

def guess_filename(file_url: str, headers: dict) -> str:
    disposition = headers.get("Content-Disposition", "")
    match = re.search(r'filename="?([^";]+)"?', disposition)
    if match:
        return match.group(1)

    parsed = urlparse(file_url)
    name = os.path.basename(parsed.path)
    return name or "file"

def generate_uuid():
    return str(uuid.uuid4())


translit_map = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'e', 'ж': 'zh','з': 'z', 'и': 'i',
    'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm','н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's','т': 't',
    'у': 'u', 'ф': 'f', 'х': 'h','ц': 'ts','ч': 'ch',
    'ш': 'sh','щ': 'sch','ъ': '', 'ы': 'y','ь': '',
    'э': 'e', 'ю': 'yu','я': 'ya'
}

translit_map.update({k.upper(): v.capitalize() for k, v in translit_map.items()})

def normalize_command(command: str) -> str:
    command = command.replace(" ", "")
    command = command.lower()
    result = ''
    for char in command:
        if char in translit_map:
            result += translit_map[char]
        elif char.isalnum():
            result += char
    return result

def clean_commands(commands: dict) -> dict:
    for cmd in commands["commands"]:
        cmd["command"] = normalize_command(cmd["command"])
    return commands


def extract_telegram_attachments(message: dict, token: str):
    """Return attachments list and message type for a Telegram message."""
    attachments = []
    message_type = None

    if "photo" in message:
        photo = message["photo"][-1]
        file_id = photo["file_id"]
        attachments.append({
            "type": "Image",
            "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
            "mime": "image/jpeg",
        })
        message_type = "photo"
    elif "voice" in message:
        file_id = message["voice"]["file_id"]
        attachments.append({
            "type": "Voice",
            "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
            "mime": "audio/ogg",
        })
        message_type = "voice"
    elif "video" in message:
        file_id = message["video"]["file_id"]
        attachments.append({
            "type": "Video",
            "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
            "mime": "video/mp4",
        })
        message_type = "video"
    elif "audio" in message:
        file_id = message["audio"]["file_id"]
        attachments.append({
            "type": "Audio",
            "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
            "mime": "audio/mpeg",
        })
        message_type = "audio"
    elif "document" in message:
        file_id = message["document"]["file_id"]
        attachments.append({
            "type": "Document",
            "url": f"https://api.telegram.org/file/bot{token}/{file_id}",
            "mime": "application/octet-stream",
        })
        message_type = "document"

    return attachments, message_type
