from pydantic import BaseModel, SecretStr

class BotRegisterRequest(BaseModel):
    telegram_token: SecretStr 