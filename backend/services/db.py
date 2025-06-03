
from constants.postgres_models import session, Bot
import constants.redis_models as rdb


def create_new_bot(bot_id: int, token: str):
    exists = session.get(Bot, bot_id)
    if exists:
        return

    new_bot = Bot(bot_id = bot_id)
    new_bot.set_token(token)

    session.add(new_bot)
    session.commit()

    rdb.Bot.create(bot_id, token)

def get_bot_token(bot_id: int):
    cached = rdb.Bot.get(bot_id)
    if cached is not None:
        return cached
    

    bot = session.query(Bot).filter_by(bot_id=bot_id).first()
    if bot is None:
        return None
    
    token = bot.get_token()

    rdb.Bot.create(bot_id, token)

    return token

def delete_bot(bot_id: int):
    bot = session.query(Bot).filter_by(bot_id=bot_id).first()
    if bot:
        session.delete(bot)
        session.commit()

    rdb.Bot.delete(bot_id)
