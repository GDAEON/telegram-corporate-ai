from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from constants.request_models import IntegrateUserRequest
from config.settings import INTEGRATION_URL, INTEGRATION_CODE, INTEGRATION_TOKEN, USER_NAME, USER_EMAIL
import httpx
import services.db as db
from services.webhook_server import get_bot_name, get_bot_id

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/user")
async def integrate_new_user(request: IntegrateUserRequest):
    # bot_info = {
    #     "externalId": request.userId,
    #     "name": USER_NAME,
    #     "locale": "ru",
    #     "timeZone": "+03:00",
    #     "email": USER_EMAIL,
    #     "paymentType": "internal",
    #     "status": {
    #         "status": "active",
    #         "paymentStatus": "trial",
    #         "expiresAt": "2022-04-11T07:32:43.329+00:00"
    #     }
    # }

    # headers = {
    #     "Authorization": f"Bearer {INTEGRATION_TOKEN}",
    #     "Content-Type": "application/json"
    # }

    # async with httpx.AsyncClient() as client:
    #     response = await client.post(f"{INTEGRATION_URL}/{INTEGRATION_CODE}", json=bot_info, headers=headers)

    # if response.status_code >= 400:
    #     raise HTTPException(status_code=response.status_code, detail=response.text)

    # if response.content:
    #     try:
    #         return response.json()
    #     except Exception:
    #         return {"status": "ok", "raw_response": response.text}
    # else:
    #     return {"status": "ok", "message": "No content"}

    
    user_id = request.userId
    name = USER_NAME
    email = USER_EMAIL
    token = request.token.get_secret_value()
    bot_id = await get_bot_id(token)
    bot_name = await get_bot_name(token)

    if bot_id and bot_name:

        owner = db.get_owner(user_id)

        if owner is not None:
            if not db.owner_has_bot(user_id, bot_id):
                db.add_bot_to_owner(bot_id, bot_name, token, owner)
            else:
                return JSONResponse(content={"message": "Already connected"}, status_code=409)
        else:
            db.create_new_owner(user_id, name, email, bot_id, bot_name, token)

        return "OK"
    
    return JSONResponse(content={"message": "Invalid bot token"}, status_code=401)
    

