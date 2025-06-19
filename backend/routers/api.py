from typing import Optional
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, Response

from constants.request_models import IntegrateRequest
from constants.response_models import (
    IntegrationResponse,
    UsersPageResponse,
)
from config.settings import (
    INTEGRATION_URL,
    INTEGRATION_CODE,
    INTEGRATION_TOKEN,
    WEBHOOK_URL,
)
import httpx
import services.helper_functions as hf
import services.db as db
from services.webhook_server import get_bot_name, get_bot_id, set_webhook

router = APIRouter(prefix="/api", tags=["API"])


@router.post(
    "/bot",
    response_model=IntegrationResponse,
    description=(
        "Register a Telegram bot in the corporate service. "
        "Expects IntegrateRequest with the bot token and owner UUID."),
)
async def integrate_new_user(request: IntegrateRequest):
    """Integrate a new bot or update an existing one."""
    token = request.telegram_token.get_secret_value()
    owner_uuid = request.owner_uuid.get_secret_value()
    locale = request.locale or "en"

    bot_id = await get_bot_id(token)
    bot_name = await get_bot_name(token)

    if not bot_id or not bot_name:
        raise HTTPException(status_code=401, detail="Invalid bot token")

    bot_exists = db.bot_exists(bot_id)

    if bot_exists:
        stored_name, pass_uuid, _, stored_locale = db.get_bot_auth(bot_id)
        bot_name = stored_name
        locale = request.locale or stored_locale or "en"
        if locale != stored_locale:
            db.update_bot_locale(bot_id, locale)
    else:
        pass_uuid = hf.generate_uuid()

        set_webhook_response = await set_webhook(
            token, f"{WEBHOOK_URL}/webhook/{bot_id}"
        )

        if set_webhook_response["status_code"] != 200:
            raise HTTPException(status_code=500, detail="Failed to set webhook")

    integration_request = {
        "externalId": "12",  # TODO replace with bot_id
        "name": str(bot_name),
        "locale": locale,
        "paymentType": "external",
        "status": {
            "status": "active",
        },
    }

    headers = {
        "Authorization": f"Bearer {INTEGRATION_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            integration_response = await client.post(
                f"{INTEGRATION_URL}/{INTEGRATION_CODE}",
                json=integration_request,
                headers=headers,
            )

        data = integration_response.json()

        if "webUrl" in data:
            web_url = data["webUrl"]
        else:
            try:
                error_detail = integration_response.json()
            except Exception:
                error_detail = integration_response.text
            raise HTTPException(
                status_code=integration_response.status_code,
                detail=error_detail,
            )

        if bot_exists:
            db.update_bot_web_url(bot_id, web_url)
        else:
            db.create_new_bot(
                bot_id,
                token,
                bot_name,
                owner_uuid,
                pass_uuid,
                web_url,
                locale,
            )

        return IntegrationResponse(
            botName=bot_name, passUuid=pass_uuid, webUrl=web_url, botId=bot_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@router.get(
    "/owner/{owner_uuid}/bots",
    description="List all bots registered by the given owner UUID",
)
async def bots_by_owner(owner_uuid: str):
    """Return list of bots for a given owner."""
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


@router.get(
    "/{bot_id}/isVerified",
    description="Check if a bot was verified by its owner",
)
async def is_bot_verified(bot_id: int):
    """Return verification status of the bot."""
    return db.is_bot_verified(bot_id)


@router.get(
    "/{bot_id}/users",
    response_model=UsersPageResponse,
    description=(
        "List bot users. Supports pagination, search and status filtering."),
)
async def list_bot_users(
    bot_id: int,
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    status: Optional[bool] = None,
):
    """Return paginated users for the given bot."""
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


@router.get(
    "/{bot_id}/owner",
    description="Return stored owner name for the bot",
)
async def owner_name(bot_id: int) -> str:
    """Return bot owner's display name."""
    try:
        owner_name = db.get_owner_name(bot_id)

        return owner_name
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{bot_id}/authInfo",
    description="Return authentication info for admin panel login",
)
async def auth_info(bot_id: int):
    """Return bot name, pass token and admin panel url."""
    try:
        bot_name, pass_uuid, web_url, _ = db.get_bot_auth(bot_id)

        return {"botName": bot_name, "passUiid": pass_uuid, "webUrl": web_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/bot/{bot_id}/refresh",
    response_model=IntegrationResponse,
    description="Request a new admin panel URL for the bot",
)
async def refresh_web_url(bot_id: int, locale: Optional[str] = None):
    """Fetch a new admin panel URL for the bot."""
    if not db.bot_exists(bot_id):
        raise HTTPException(status_code=404, detail="Bot not found")

    bot_name, pass_uuid, _, stored_locale = db.get_bot_auth(bot_id)
    locale = locale or stored_locale or "en"

    integration_request = {
        "externalId": "12",  # TODO replace with bot_id
        "name": str(bot_name),
        "locale": locale,
        "paymentType": "external",
        "status": {"status": "active"},
    }

    headers = {
        "Authorization": f"Bearer {INTEGRATION_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient() as client:
            integration_response = await client.post(
                f"{INTEGRATION_URL}/{INTEGRATION_CODE}",
                json=integration_request,
                headers=headers,
            )

        data = integration_response.json()
        if "webUrl" not in data:
            try:
                error_detail = integration_response.json()
            except Exception:
                error_detail = integration_response.text
            raise HTTPException(
                status_code=integration_response.status_code,
                detail=error_detail,
            )

        web_url = data["webUrl"]
        db.update_bot_web_url(bot_id, web_url)

        return IntegrationResponse(
            botName=bot_name, passUuid=pass_uuid, webUrl=web_url, botId=bot_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


@router.post(
    "/bot/{bot_id}/invite",
    description="Generate a single use invitation token for a bot",
)
async def generate_invite(bot_id: int):
    """Generate a single-use pass UUID for inviting a user."""
    if not db.bot_exists(bot_id):
        raise HTTPException(status_code=404, detail="Bot not found")
    try:
        new_uuid = db.create_pass_token(bot_id)
        return {"passUuid": new_uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/bot/{bot_id}/logout",
    description="Mark bot as unverified forcing owner to login again",
)
async def logout_owner(bot_id: int):
    """Log out owner from admin panel."""
    try:
        db.bot_set_verified(bot_id, False)
        return {"botId": bot_id, "verified": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/bot/{bot_id}/user/{user_id}",
    description="Change active status of a bot user",
)
async def switch_activness(bot_id: int, user_id: int, new_status: bool):
    """Activate or deactivate a user."""
    try:
        db.set_botuser_status(bot_id, user_id, new_status)
        return {"user_id": user_id, "is_active": new_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/bot/{bot_id}/user/{user_id}",
    description="Remove a user from a bot and delete all data",
)
async def delete_user(bot_id: int, user_id: int):
    """Delete a user from the database."""
    try:
        db.delete_user_by_id(user_id)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
