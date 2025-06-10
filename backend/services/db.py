from constants.postgres_models import session, Bot
from typing import Optional, Tuple
from sqlalchemy import exists
import constants.redis_models as rdb


def create_new_bot(id: int, token: str, name: str, owner_uuid: str, pass_uuid: str, web_url: str):
    new_bot = Bot(id=id, name=name)
    
    new_bot.set_token(token)
    new_bot.set_owner_uuid(owner_uuid)
    new_bot.set_pass_uuid(pass_uuid)
    new_bot.set_web_url(web_url)

    session.add(new_bot)
    session.commit()

def bot_exists(id: int) -> bool:
    return session.query(exists().where(Bot.id == id)).scalar()

def get_bot_auth(id: int) -> Optional[Tuple[str, str]]:
    bot = session.query(Bot).filter(Bot.id == id).first()

    pass_uuid = bot.get_pass_uuid()
    web_url = bot.get_web_url()

    return pass_uuid, web_url





