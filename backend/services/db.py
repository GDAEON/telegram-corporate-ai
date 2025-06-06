from constants.postgres_models import session, Bot, Owner
from typing import Optional
from sqlalchemy import exists
import constants.redis_models as rdb


def get_bot_token(bot_id: int):
    cached = rdb.Bot.get(bot_id)
    if cached is not None:
        return cached
    

    bot = session.query(Bot).filter_by(bot_id=bot_id).first()
    if bot is None:
        return None
    
    token = bot.get_token()

    return token

def delete_bot(bot_id: int):
    bot = session.query(Bot).filter_by(bot_id=bot_id).first()
    if bot:
        session.delete(bot)
        session.commit()

def create_new_owner(id: int, name: str, email: str, bot_id: int, bot_name: str, token: str):
    new_owner = Owner(id=id, name=name, email=email)

    session.add(new_owner)
    session.commit()

    new_bot = Bot(bot_id=bot_id, name=bot_name)
    new_bot.set_token(token)
    new_bot.owner = new_owner

    session.add(new_bot)
    session.commit()


def get_owner(id: int) -> Optional[Owner]:
    return session.query(Owner).filter_by(id=id).first()

def owner_has_bot(id: int, bot_id: int):
    return session.query(
        exists().where(
            (Bot.bot_id == bot_id) &
            (Bot.owner_id == id)
        )
    ).scalar()

def add_bot_to_owner(bot_id: int, bot_name: str, token: str, owner: Owner):
    new_bot = Bot(bot_id=bot_id, name=bot_name)
    new_bot.set_token(token)
    new_bot.owner = owner

    session.add(new_bot)
    session.commit()

def delete_owner(id: int):
    owner = session.query(Owner).filter_by(id=id).first()
    if owner:
        session.delete(owner)
        session.commit()


def owner_has_only_one_bot(id: int) -> bool:
    bots = session.query(Bot.bot_id).filter(Bot.owner_id == id).limit(2).all()
    return len(bots) == 1
