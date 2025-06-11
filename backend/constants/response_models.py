from pydantic import BaseModel

class IntegrationResponse(BaseModel):
    botName: str
    passUuid: str
    webUrl: str
    botId: int


class UserInfo(BaseModel):
    id: int
    name: str | None = None
    surname: str | None = None
    phone: str | None = None
    isOwner: bool
    status: bool


class UsersPageResponse(BaseModel):
    users: list[UserInfo]
    total: int
