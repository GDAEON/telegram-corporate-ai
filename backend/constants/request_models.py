from pydantic import BaseModel, SecretStr
from typing import Optional, List, Dict, Any

class ExtraData(BaseModel):
    additionalProp1: Optional[Dict[str, Any]] = None


class Chat(BaseModel):
    externalId: str
    messengerInstance: str
    contact: str
    operator: Optional[str] = None
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
    mime: Optional[str] = None
    url: Optional[str] = None

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
    caption: Optional[str] = None


class IntegrateRequest(BaseModel):
    telegram_token: SecretStr

class Job(BaseModel):
    job: str
    targets: List[str]