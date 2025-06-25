import httpx
from typing import Any, Dict
from services.logging_setup import interaction_logger

async def get_bot_id(token: str) -> int:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = resp.json()

        if data['ok'] == False:
            interaction_logger.error("Failed to fetch bot id")
            return None

        bot_id = data["result"]["id"]
        interaction_logger.info(f"Fetched bot id {bot_id}")
        return bot_id

async def get_bot_name(token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = resp.json()

        if data['ok'] == False:
            interaction_logger.error("Failed to fetch bot name")
            return None

        name = data["result"]["username"]
        interaction_logger.info(f"Fetched bot name {name}")
        return name


async def set_webhook(TOKEN: str, WEBHOOK_URL: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'https://api.telegram.org/bot{TOKEN}/setWebhook',
            data={"url": WEBHOOK_URL}
        )

        interaction_logger.info(
            f"Set webhook for bot token ending {TOKEN[-4:]} status={response.status_code}"
        )

        return {
            "status_code": response.status_code,
            "body": response.json()
        }
    

async def delete_webhook(token: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    async with httpx.AsyncClient() as client:
        response = await client.post(url)

        interaction_logger.info(
            f"Delete webhook status={response.status_code}"
        )
        
        return {
            "status_code": response.status_code,
            "body": response.json()
        }