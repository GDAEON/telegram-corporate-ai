from contextlib import contextmanager
from cryptography.fernet import InvalidToken
from typing import Optional, Tuple

from sqlalchemy import exists, or_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from constants.postgres_models import engine, Bot, User, BotUser
from constants import redis_models as rdb

SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session():
    
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

    rdb.Bot.create(id, token)
    rdb.Bot.set_auth(id, name, owner_uuid, pass_uuid, web_url)


def bot_exists(id: int) -> bool:
    if rdb.Bot.exists(id):
        return True
    with get_session() as session:
        exists_db = session.query(exists().where(Bot.id == id)).scalar()
        if exists_db:
            bot = session.get(Bot, id)
            if bot:
                rdb.Bot.create(id, bot.get_token())
                rdb.Bot.set_auth(id, bot.name, bot.get_owner_uuid(), bot.get_pass_uuid(), bot.get_web_url())
        return exists_db


def get_bot_auth(id: int) -> Optional[Tuple[str, str, str]]:
    """Return bot name, pass uuid and web url for the bot."""
    cached = rdb.Bot.get_auth(id)
    if cached:
        return cached["name"], cached["pass_uuid"], cached["web_url"]

    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return None
        rdb.Bot.set_auth(id, bot.name, bot.get_owner_uuid(), bot.get_pass_uuid(), bot.get_web_url())
        rdb.Bot.create(id, bot.get_token())
        return bot.name, bot.get_pass_uuid(), bot.get_web_url()


def compare_bot_auth_owner(id: int, tested_owner_uuid: str) -> bool:
    cached = rdb.Bot.get_auth(id)
    if cached and cached.get("owner_uuid") == tested_owner_uuid:
        return True
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return False
        rdb.Bot.set_auth(id, bot.name, bot.get_owner_uuid(), bot.get_pass_uuid(), bot.get_web_url())
        rdb.Bot.create(id, bot.get_token())
        return bool(bot.get_owner_uuid() == tested_owner_uuid)


def compare_bot_auth_pass(id: int, tested_pass_uuid: str) -> bool:
    """Return True if pass uuid matches the stored value"""
    cached = rdb.Bot.get_auth(id)
    if cached and cached.get("pass_uuid") == tested_pass_uuid:
        return True
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return False
        rdb.Bot.set_auth(id, bot.name, bot.get_owner_uuid(), bot.get_pass_uuid(), bot.get_web_url())
        rdb.Bot.create(id, bot.get_token())
        return bool(bot.get_pass_uuid() == tested_pass_uuid)


def get_bot_by_owner_uuid(owner_uuid: str) -> Optional[Tuple[int, str, str, str]]:
    """Return bot info by owner uuid."""
    with get_session() as session:
        bots = session.query(Bot).all()
        for bot in bots:
            if bot.get_owner_uuid() == owner_uuid:
                return bot.id, bot.name, bot.get_pass_uuid(), bot.get_web_url()
    return None


def get_bots_by_owner_uuid(owner_uuid: str) -> list[Tuple[int, str, str, str]]:
    """Return list of bot info tuples for the given owner uuid."""
    with get_session() as session:
        bots = session.query(Bot).all()
        res = []
        for bot in bots:
            if bot.get_owner_uuid() == owner_uuid:
                res.append((bot.id, bot.name, bot.get_pass_uuid(), bot.get_web_url()))
        return res


def get_bot_token(id: int) -> Optional[str]:
    cached = rdb.Bot.get(id)
    if cached is not None:
        return cached
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return None
        token = bot.get_token()
        rdb.Bot.create(id, token)
        rdb.Bot.set_auth(id, bot.name, bot.get_owner_uuid(), bot.get_pass_uuid(), bot.get_web_url())
        return token


def is_bot_verified(id: int) -> bool:
    with get_session() as session:
        bot = session.get(Bot, id)
        return bool(bot and bot.verified)


def add_owner_user(bot_id: int, user_id: int):
    
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            session.add(user)
            session.flush()

        bu = (
            session.query(BotUser)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .one_or_none()
        )
        if bu:
            bu.is_owner = True
            bu.is_active = True
        else:
            session.add(BotUser(bot_id=bot_id, user_id=user_id, is_owner=True, is_active=True))

        phone = None
        if user.phone:
            try:
                phone = user.get_phone()
            except InvalidToken:
                phone = user.phone
        rdb.User.set(user_id, user.name, user.surname, phone)

    rdb.Bot.set_owner_id(bot_id, user_id)


def get_is_bot_owner(bot_id: int, user_id: int) -> bool:
    cached_owner_id = rdb.Bot.get_owner_id(bot_id)
    if cached_owner_id is not None:
        return cached_owner_id == user_id
    with get_session() as session:
        row = (
            session.query(BotUser.is_owner)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .first()
        )
        if row and row[0]:
            rdb.Bot.set_owner_id(bot_id, user_id)
            return True
        return False


def owner_has_contact(bot_id: int, user_id: int) -> bool:
    """Return True if the owner has provided phone contact."""
    cached = rdb.User.get(user_id)
    if cached and cached.get("phone"):
        return True
    with get_session() as session:
        row = (
            session.query(User.phone)
                   .join(BotUser, User.id == BotUser.user_id)
                   .filter(
                       BotUser.bot_id == bot_id,
                       BotUser.user_id == user_id,
                       BotUser.is_owner.is_(True),
                   )
                   .first()
        )
        return bool(row and row[0])


def get_bot_owner_id(bot_id: int) -> Optional[int]:
    """Return user id of the bot owner if exists."""
    cached = rdb.Bot.get_owner_id(bot_id)
    if cached is not None:
        return cached
    with get_session() as session:
        row = (
            session.query(BotUser.user_id)
                   .filter_by(bot_id=bot_id, is_owner=True)
                   .first()
        )
        if row:
            rdb.Bot.set_owner_id(bot_id, row[0])
            return row[0]
        return None


def update_user(user_id: int, name: str, surname: str, phone: str):
    with get_session() as session:
        user = session.query(User).filter_by(id=user_id).one_or_none()
        if not user:
            return
        user.name = name
        user.surname = surname
        user.set_phone(phone)
    rdb.User.set(user_id, name, surname, phone)


def add_user_to_a_bot(
    bot_id: int,
    user_id: int,
    name: str,
    surname: str,
    phone: str | None = None,
):
    
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            user = User(id=user_id, name=name, surname=surname)
            if phone:
                user.set_phone(phone)
            session.add(user)
            session.flush()
        else:
            user.name = name
            user.surname = surname
            if phone:
                user.set_phone(phone)

        bu = (
            session.query(BotUser)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .one_or_none()
        )
        if not bu:
            session.add(BotUser(bot_id=bot_id, user_id=user_id, is_active=True))

        phone_val = None
        if user.phone:
            try:
                phone_val = user.get_phone()
            except InvalidToken:
                phone_val = user.phone
        rdb.User.set(user_id, user.name, user.surname, phone_val)


def bot_has_user(bot_id: int, user_id: int) -> bool:
    with get_session() as session:
        return session.query(
            exists().where(
                (BotUser.bot_id == bot_id) & (BotUser.user_id == user_id)
            )
        ).scalar()


def get_botuser_status(bot_id: int, user_id: int) -> Optional[bool]:
    """Return True/False if user exists, None if not registered"""
    with get_session() as session:
        row = (
            session.query(BotUser.is_active)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .first()
        )
        return row[0] if row else None


def bot_set_verified(id: int, new_verified: bool):
    with get_session() as session:
        bot = session.get(Bot, id)
        if bot:
            bot.verified = new_verified


def get_bot_users(
    bot_id: int,
    page: int = 1,
    per_page: int = 10,
    search: str | None = None,
    is_active: bool | None = None,
):
    with get_session() as session:
        query = (
            session.query(User, BotUser)
            .join(BotUser, User.id == BotUser.user_id)
            .filter(BotUser.bot_id == bot_id)
        )

        if search:
            pattern = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.name).like(pattern),
                    func.lower(User.surname).like(pattern),
                )
            )

        if is_active is not None:
            query = query.filter(BotUser.is_active == is_active)

        total = query.count()

        rows = (
            query.order_by(User.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        users = []
        for user, bu in rows:
            cached = rdb.User.get(user.id)
            if cached:
                name = cached.get("name")
                surname = cached.get("surname")
                phone = cached.get("phone")
            else:
                raw_phone = user.phone
                if raw_phone:
                    try:
                        phone = user.get_phone()
                    except InvalidToken:
                        phone = raw_phone
                else:
                    phone = None
                name = user.name
                surname = user.surname
                rdb.User.set(user.id, name, surname, phone)

            users.append({
                "id": user.id,
                "name": name,
                "surname": surname,
                "phone": phone,
                "isOwner": bu.is_owner,
                "status": bu.is_active,
            })
        return users, total

def get_owner_name(bot_id: int) -> Optional[str]:
    owner_id = rdb.Bot.get_owner_id(bot_id)
    with get_session() as session:
        if owner_id is not None:
            cached = rdb.User.get(owner_id)
            if cached:
                full = f"{cached.get('name') or ''} {cached.get('surname') or ''}".strip()
                if full:
                    return full
            user = session.get(User, owner_id)
            if user:
                phone_val = None
                if user.phone:
                    try:
                        phone_val = user.get_phone()
                    except InvalidToken:
                        phone_val = user.phone
                rdb.User.set(owner_id, user.name, user.surname, phone_val)
                full = f"{user.name or ''} {user.surname or ''}".strip()
                return full or None

        stmt = (
            select(User.name, User.surname, User.id)
            .join(BotUser, BotUser.user_id == User.id)
            .where(BotUser.bot_id == bot_id, BotUser.is_owner.is_(True))
            .limit(1)
        )
        result = session.execute(stmt).first()

        if not result:
            return None

        name, surname, uid = result
        rdb.Bot.set_owner_id(bot_id, uid)
        full = f"{name or ''} {surname or ''}".strip()
        return full or None

def set_botuser_status(bot_id: int, user_id: int, new_status: bool) -> None:
    with get_session() as session:
        session.query(BotUser) \
               .filter(
                   BotUser.bot_id == bot_id,
                   BotUser.user_id == user_id
               ) \
               .update({"is_active": new_status}, synchronize_session=False)
        session.commit()

def delete_user_by_id(user_id: int) -> None:
    with get_session() as session:
        session.query(User) \
               .filter(User.id == user_id) \
               .delete(synchronize_session=False)
        session.commit()
    rdb.User.delete(user_id)


def delete_botuser(bot_id: int, user_id: int) -> None:
    with get_session() as session:
        session.query(BotUser) \
               .filter(
                   BotUser.bot_id == bot_id,
                   BotUser.user_id == user_id
               ) \
               .delete(synchronize_session=False)
        session.commit()
