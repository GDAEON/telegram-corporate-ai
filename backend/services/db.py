from contextlib import contextmanager
from typing import Optional, Tuple

from sqlalchemy import exists
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from constants.postgres_models import engine, Bot, User, BotUser

SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session():
    """
    Provide a transactional scope around a series of operations.
    Rolls back on error, commits on success, and closes session.
    """
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()


def create_new_bot(
    id: int,
    token: str,
    name: str,
    owner_uuid: str,
    pass_uuid: str,
    web_url: str,
):
    with get_session() as session:
        new_bot = Bot(id=id, name=name)
        new_bot.set_token(token)
        new_bot.set_owner_uuid(owner_uuid)
        new_bot.set_pass_uuid(pass_uuid)
        new_bot.set_web_url(web_url)
        session.add(new_bot)


def bot_exists(id: int) -> bool:
    with get_session() as session:
        return session.query(exists().where(Bot.id == id)).scalar()


def get_bot_auth(id: int) -> Optional[Tuple[str, str]]:
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return None
        return bot.get_pass_uuid(), bot.get_web_url()


def compare_bot_auth_owner(id: int, tested_owner_uuid: str) -> bool:
    with get_session() as session:
        bot = session.get(Bot, id)
        return bool(bot and bot.get_owner_uuid() == tested_owner_uuid)


def get_bot_token(id: int) -> Optional[str]:
    with get_session() as session:
        bot = session.get(Bot, id)
        return bot.get_token() if bot else None


def is_bot_verified(id: int) -> bool:
    with get_session() as session:
        bot = session.get(Bot, id)
        return bool(bot and bot.verified)


def add_owner_user(bot_id: int, user_id: int):
    """
    Adds or promotes an existing user to be an owner of the bot.
    Skips duplicate insertion and updates flags if already present.
    """
    with get_session() as session:
        # ensure user exists
        user = session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            session.add(user)
            session.flush()

        # upsert BotUser
        bu = (
            session.query(BotUser)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .one_or_none()
        )
        if bu:
            bu.is_owner = True
            bu.is_active = True
        else:
            session.add(
                BotUser(bot_id=bot_id, user_id=user_id, is_owner=True, is_active=True)
            )


def get_is_bot_owner(bot_id: int, user_id: int) -> bool:
    with get_session() as session:
        row = (
            session.query(BotUser.is_owner)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .first()
        )
        return bool(row and row[0])


def update_user(user_id: int, name: str, surname: str, phone: str):
    with get_session() as session:
        user = session.query(User).filter_by(id=user_id).one_or_none()
        if not user:
            return
        user.name = name
        user.surname = surname
        user.set_phone(phone)


def add_user_to_a_bot(
    bot_id: int,
    user_id: int,
    name: str,
    surname: str,
    phone: str,
):
    """
    Adds a user to a bot's users list, skipping duplicates.
    """
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            user = User(id=user_id, name=name, surname=surname)
            user.set_phone(phone)
            session.add(user)
            session.flush()

        bu = (
            session.query(BotUser)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .one_or_none()
        )
        if not bu:
            session.add(BotUser(bot_id=bot_id, user_id=user_id, is_active=True))


def bot_has_user(bot_id: int, user_id: int) -> bool:
    with get_session() as session:
        return session.query(
            exists().where(
                (BotUser.bot_id == bot_id) & (BotUser.user_id == user_id)
            )
        ).scalar()


def bot_set_verified(id: int, new_verified: bool):
    with get_session() as session:
        bot = session.get(Bot, id)
        if bot:
            bot.verified = new_verified
