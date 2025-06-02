import httpx
from io import BytesIO
from services.helper_functions import guess_filename

async def send_message(token:str, chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        })

        return {
            "status_code": response.status_code,
            "body": response.json()
        }
    
    
async def send_media(token: str, chat_id: int, file_type: str, file_url: str, file_mime: str, caption: str):
    async with httpx.AsyncClient() as client:
        file_response = await client.get(file_url, follow_redirects=True)
        file_response.raise_for_status()

        content = file_response.content
        file_size = len(content)

        method_map = {
            "image": ("sendPhoto", "photo", 5 * 1024 * 1024),
            "video": ("sendVideo", "video", 20 * 1024 * 1024),
            "document": ("sendDocument", "document", 20 * 1024 * 1024),
            "audio": ("sendAudio", "audio", 5 * 1024 * 1024),
            "voice": ("sendVoice", "voice", 1 * 1024 * 1024)
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