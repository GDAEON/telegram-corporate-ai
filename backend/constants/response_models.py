from pydantic import BaseModel

class IntegrationResponse(BaseModel):
    botName: str
    passUuid: str
    webUrl: str
