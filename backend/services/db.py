from constants.postgres_models import session, Bot, User, BotUser
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

def compare_bot_auth_owner(id: int, tested_owner_uuid: str) -> bool:
    bot = session.query(Bot).filter(Bot.id == id).first()

    owner_uuid = bot.get_owner_uuid()

    return owner_uuid == tested_owner_uuid

def get_bot_token(id: int) -> str:
    bot = session.query(Bot).filter(Bot.id == id).first()
    return bot.get_token()

def is_bot_verified(id: int) -> bool:
    bot = session.query(Bot).filter(Bot.id == id).first()
    if not bot:
        return False
    return bot.isVerified

def add_user_to_a_bot(bot_id: int, user_id: int, name: str, surname: str, phone: str):
    user = session.query(User).filter_by(id=user_id).one_or_none()
    if user is None:
        user = User(id=user_id, name=name, surname=surname)
        user.set_phone(phone)
        session.add(user)
        session.flush()

    bot = session.query(Bot).get(bot_id)
    bot.users.append(BotUser(user=user))

    session.commit()

def bot_has_user(bot_id: int, user_id: int) -> bool:
    return session.query(
            exists().where(
                (BotUser.bot_id == bot_id) &
                (BotUser.user_id == user_id)
            )
        ).scalar()

def bot_set_verified(id: int, new_verified: bool):
    bot = session.query(Bot).get(id)
    bot.verified = new_verified
    session.commit()


