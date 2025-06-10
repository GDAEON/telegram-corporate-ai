import httpx
from typing import Any, Dict

async def get_bot_id(token: str) -> int:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = resp.json()

        if data['ok'] == False:
            return None
        
        return data["result"]["id"]

async def get_bot_name(token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = resp.json()

        if data['ok'] == False:
            return None

        return data["result"]["username"]


async def set_webhook(TOKEN: str, WEBHOOK_URL: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'https://api.telegram.org/bot{TOKEN}/setWebhook',
            data={"url": WEBHOOK_URL}
        )

        return {
            "status_code": response.status_code,
            "body": response.json()
        }
    

async def delete_webhook(token: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    async with httpx.AsyncClient() as client:
        response = await client.post(url)
        
        return {
            "status_code": response.status_code,
            "body": response.json()
        }