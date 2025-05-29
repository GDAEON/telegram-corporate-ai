from pydantic import BaseModel, SecretStr
from typing import Optional

class BotRegisterRequest(BaseModel):
    telegram_token: SecretStr 

class BotUnregisterRequest(BaseModel):
    token: Optional[SecretStr] = None
    bot_id: Optional[int] = None