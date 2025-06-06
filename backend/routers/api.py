from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from constants.request_models import IntegrateUserRequest
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN, WEBHOOK_URL, USER_NAME, USER_EMAIL
import httpx
import services.db as db
from services.webhook_server import get_bot_name, get_bot_id, set_webhook

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/user")
async def integrate_new_user(request: IntegrateUserRequest):    
    user_id = request.userId
    name = USER_NAME
    email = USER_EMAIL
    token = request.token.get_secret_value()
    bot_id = await get_bot_id(token)
    bot_name = await get_bot_name(token)

    if bot_id and bot_name:
        owner = db.get_owner(user_id)

        is_new_owner = False
        if owner is not None:
            if not db.owner_has_bot(user_id, bot_id):
                db.add_bot_to_owner(bot_id, bot_name, token, owner)
            else:
                return JSONResponse(content={"message": "Already connected"}, status_code=409)
        else:
            db.create_new_owner(user_id, name, email, bot_id, bot_name, token)
            is_new_owner = True  

        bot_info = {
            "externalId": str(user_id),
            "name": USER_NAME,
            "locale": "ru",
            "timeZone": "+03:00",
            "email": USER_EMAIL,
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

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{INTEGRATION_URL}/{INTEGRATION_CODE}",
                    json=bot_info,
                    headers=headers
                )

            if response.status_code >= 400:
                if is_new_owner or db.owner_has_only_one_bot(user_id):
                    db.delete_owner(user_id)
                else:
                    db.delete_bot(bot_id)
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            webhook_response = await set_webhook(token, f"{WEBHOOK_URL}/webhook/{bot_id}")

            if response.content:
                try:
                    main_response_json = response.json()
                except Exception as e:
                    return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
            else:
                return JSONResponse(content={"status": "not ok", "message": "No content"}, status_code=502)
            
            if not webhook_response.get("ok", True): 
                if is_new_owner or db.owner_has_only_one_bot(user_id):
                    db.delete_owner(user_id)
                else:
                    db.delete_bot(bot_id)
                return JSONResponse(content={"status": "error", "message": "Webhook setup failed", "webhook": webhook_response}, status_code=500)
            
            combined_response = {
                **main_response_json,
                "webhook": webhook_response
            }

            return JSONResponse(content=combined_response, status_code=200)

        except Exception as e:
            if is_new_owner or db.owner_has_only_one_bot(user_id):
                db.delete_owner(user_id)
            else:
                db.delete_bot(bot_id)
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

    return JSONResponse(content={"message": "Invalid bot token"}, status_code=401)

    

