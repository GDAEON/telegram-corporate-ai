from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from constants.request_models import IntegrateRequest
from constants.response_models import IntegrationResponse
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN, WEBHOOK_URL
import httpx
import services.helper_functions as hf
import services.db as db
from services.webhook_server import get_bot_name, get_bot_id, set_webhook

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/bot", response_model=IntegrationResponse)
async def integrate_new_user(request: IntegrateRequest):
    token = request.telegram_token.get_secret_value()

    bot_id = await get_bot_id(token)
    bot_name = await get_bot_name(token)

    if not bot_id or not bot_name:
        raise HTTPException(status_code=401, detail="Invalid bot token")
    
    if db.bot_exists(bot_id):
        owner_uuid, web_url = db.get_bot_auth(bot_id)

        return IntegrationResponse(ownerUuid=owner_uuid, webUrl=web_url)
    
    owner_uuid = hf.generate_uuid()
    pass_uuid = hf.generate_uuid()

    set_webhook_response = await set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

    if set_webhook_response["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to set webhook")

    integration_request = {
        "externalId": "12", # TODO replace with bot_id
        "name": str(bot_name),
        "locale": "ru",
        "paymentType": "external",
        "status": {
            "status": "active",
        }
    }

    headers = {
        "Authorization": f"Bearer {INTEGRATION_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            integration_response = await client.post(f"{INTEGRATION_URL}/{INTEGRATION_CODE}",
            json=integration_request,
            headers=headers
            )

        data = integration_response.json()

        if "webUrl" in data:
            web_url = data["webUrl"]
        else:
            try:
                error_detail = integration_response.json()
            except Exception:
                error_detail = integration_response.text
            raise HTTPException(status_code=integration_response.status_code, detail=error_detail)
        
        db.create_new_bot(bot_id, token, bot_name, owner_uuid, pass_uuid, web_url)

        return IntegrationResponse(ownerUuid=owner_uuid, webUrl=web_url)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
        
    
    

