from typing import Optional
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, Response

from constants.request_models import IntegrateRequest
from constants.response_models import (
    IntegrationResponse,
    UsersPageResponse,
)
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN, WEBHOOK_URL
import httpx
import services.helper_functions as hf
import services.db as db
from services.webhook_server import get_bot_name, get_bot_id, set_webhook

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/bot", response_model=IntegrationResponse)
async def integrate_new_user(request: IntegrateRequest):
    token = request.telegram_token.get_secret_value()
    owner_uuid = request.owner_uuid.get_secret_value()

    bot_id = await get_bot_id(token)
    bot_name = await get_bot_name(token)

    if not bot_id or not bot_name:
        raise HTTPException(status_code=401, detail="Invalid bot token")
    
    if db.bot_exists(bot_id):
        stored_name, pass_uuid, web_url = db.get_bot_auth(bot_id)

        return IntegrationResponse(botName=stored_name, passUuid=pass_uuid, webUrl=web_url, botId=bot_id)
    
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

        return IntegrationResponse(botName=bot_name, passUuid=pass_uuid, webUrl=web_url, botId=bot_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@router.get("/owner/{owner_uuid}/bots")
async def bots_by_owner(owner_uuid: str):
    """Return list of bots for given owner uuid."""
    try:
        infos = db.get_bots_by_owner_uuid(owner_uuid)
        return [
            {
                "botId": bot_id,
                "botName": bot_name,
                "passUuid": pass_uuid,
                "webUrl": web_url,
            }
            for bot_id, bot_name, pass_uuid, web_url in infos
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/{bot_id}/isVerified")
async def is_bot_verified(bot_id: int):
    return db.is_bot_verified(bot_id)


@router.get("/{bot_id}/users", response_model=UsersPageResponse)
async def list_bot_users(
    bot_id: int,
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    status: Optional[bool] = None,
):
    try:
        users, total = db.get_bot_users(
            bot_id=bot_id,
            page=page,
            per_page=per_page,
            search=search,
            is_active=status,
        )

        return {"users": users, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_id}/owner")
async def owner_name(bot_id: int) -> str:
    try:
        owner_name = db.get_owner_name(bot_id)

        return owner_name
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_id}/authInfo")
async def auth_info(bot_id: int):
    try:
        bot_name, pass_uuid, web_url = db.get_bot_auth(bot_id)

        return {"botName": bot_name, "passUiid": pass_uuid, "webUrl": web_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/bot/{bot_id}/logout")
async def logout_owner(bot_id: int):
    """Log out owner from admin panel."""
    try:
        db.bot_set_verified(bot_id, False)
        return {"botId": bot_id, "verified": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/bot/{bot_id}/user/{user_id}")
async def switch_activness(bot_id: int, user_id: int, new_status: bool):
    try:
        db.set_botuser_status(bot_id, user_id, new_status)
        return {"user_id": user_id, "is_active": new_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bot/{bot_id}/user/{user_id}")
async def delete_user(bot_id: int, user_id: int):
    try:
        db.delete_user_by_id(user_id)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))