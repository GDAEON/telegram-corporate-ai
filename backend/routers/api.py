from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from constants.request_models import IntegrateUserRequest
from config.settings import WEBHOOK_URL, INTEGRATION_CODE, INTEGRATION_TOKEN
import httpx

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/user")
async def integrate_new_user(request: IntegrateUserRequest):
    bot_info = {
        "externalId": request.bot_id,
        "name": request.name,
        "locale": "ru",
        "timeZone": "+03:00",
        "email": request.email,
        "paymentType": "internal",
        "status": {
            "status": "active",
            "paymentStatus": "trial",
            "expiresAt": "2022-04-11T07:32:43.329+00:00"
        }
    }

    headers = {
        "Authorization": f"Bearer {INTEGRATION_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{WEBHOOK_URL}/{INTEGRATION_CODE}", json=bot_info, headers=headers)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    if response.content:
        try:
            return response.json()
        except Exception:
            return {"status": "ok", "raw_response": response.text}
    else:
        return {"status": "ok", "message": "No content"}
