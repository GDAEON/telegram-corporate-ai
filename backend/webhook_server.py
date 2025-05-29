import httpx

async def get_bot_id(token: str) -> int:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = resp.json()
        return data["result"]["id"]


async def set_webhook(TOKEN: str, WEBHOOK_URL: str) -> int:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'https://api.telegram.org/bot{TOKEN}/setWebhook',
            data={"url": WEBHOOK_URL}
        )

        return {
            "status_code": response.status_code,
            "body": response.json()
        }

