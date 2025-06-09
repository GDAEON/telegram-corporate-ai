from pydantic import BaseModel

class IntegrationResponse(BaseModel):
    ownerUuid: str
    webUrl: str
