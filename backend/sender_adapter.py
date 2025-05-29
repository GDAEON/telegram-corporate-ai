import httpx

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