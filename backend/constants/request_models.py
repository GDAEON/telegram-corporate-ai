from pydantic import BaseModel, SecretStr
from typing import Optional, List, Dict, Any

class BotRegisterRequest(BaseModel):
    telegram_token: SecretStr 

class ExtraData(BaseModel):
    additionalProp1: Optional[Dict[str, Any]] = None


class Chat(BaseModel):
    externalId: str
    messengerInstance: str
    contact: str
    operator: str
    messengerId: str
    extraData: Optional[ExtraData] = None


class QuickReply(BaseModel):
    text: str
    type: str  
    color: str 


class InlineButton(BaseModel):
    text: str
    payload: str
    color: str
    url: Optional[str] = None

class File(BaseModel):
    type: str
    url: str
    mime: str

class SendTextMessageRequest(BaseModel):
    chat: Chat
    quickReplies: Optional[List[List[QuickReply]]] = None
    inlineButtons: Optional[List[List[InlineButton]]] = None
    text: str

class SendMediaMessageRequest(BaseModel):
    chat: Chat
    quickReplies: Optional[List[List[QuickReply]]] = None
    inlineButtons: Optional[List[List[InlineButton]]] = None
    file: File
    caption: str


class IntegrateUserRequest(BaseModel):
    bot_id: str
    name: str
    email: str

class Job(BaseModel):
    job: str
    targets: List[str]