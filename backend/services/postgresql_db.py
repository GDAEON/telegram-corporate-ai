from constants.database_models import session, Bot

def create_new_bot(bot_id: int, token: str):
    new_bot = Bot(bot_id = bot_id)
    new_bot.set_token(token)

    session.add(new_bot)
    session.commit()

def get_bot_token(bot_id: int):
    bot = session.query(Bot).filter_by(bot_id=bot_id).first()
    return bot.get_token()

def delete_bot(bot_id: int):
    bot = session.query(Bot).filter_by(bot_id=bot_id).first()
    session.delete(bot)
    session.commit()
