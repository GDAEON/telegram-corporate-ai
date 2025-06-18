from contextlib import contextmanager
from cryptography.fernet import InvalidToken
from typing import Optional, Tuple

from sqlalchemy import exists, or_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from constants.postgres_models import engine, Bot, User, BotUser, Invitation
import constants.redis_models as rdb
import services.helper_functions as hf

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
    locale: str = "en",
):
    with get_session() as session:
        new_bot = Bot(id=id, name=name, locale=locale)
        new_bot.set_token(token)
        new_bot.set_owner_uuid(owner_uuid)
        new_bot.set_pass_uuid(pass_uuid)
        new_bot.set_web_url(web_url)
        session.add(new_bot)
    rdb.Bot.create(id, token)


def bot_exists(id: int) -> bool:
    with get_session() as session:
        return session.query(exists().where(Bot.id == id)).scalar()


def update_bot_web_url(id: int, new_url: str) -> None:
    """Update stored web URL for a bot."""
    with get_session() as session:
        bot = session.get(Bot, id)
        if bot:
            bot.set_web_url(new_url)


def update_bot_locale(id: int, locale: str) -> None:
    """Update stored locale for a bot."""
    with get_session() as session:
        bot = session.get(Bot, id)
        if bot:
            bot.set_locale(locale)


def get_bot_auth(id: int) -> Optional[Tuple[str, str, str, str]]:
    """Return bot name, pass uuid, web url and locale for the bot."""
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return None
        return bot.name, bot.get_pass_uuid(), bot.get_web_url(), bot.get_locale()


def compare_bot_auth_owner(id: int, tested_owner_uuid: str) -> bool:
    with get_session() as session:
        bot = session.get(Bot, id)
        return bool(bot and bot.get_owner_uuid() == tested_owner_uuid)


def create_invite(bot_id: int) -> str:
    """Create a new invitation pass uuid for a bot."""
    new_uuid = hf.generate_uuid()
    with get_session() as session:
        invite = Invitation(bot_id=bot_id)
        invite.set_pass_uuid(new_uuid)
        session.add(invite)
    return new_uuid


def use_invite(bot_id: int, pass_uuid: str, user_id: int) -> bool:
    """Validate and mark invitation as used by the user."""
    with get_session() as session:
        invites = (
            session.query(Invitation)
                   .filter(Invitation.bot_id == bot_id)
                   .all()
        )
        for invite in invites:
            if invite.get_pass_uuid() == pass_uuid:
                if invite.used_by is None:
                    invite.used_by = user_id
                    return True
                return False
        return False


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


def get_all_bots() -> list[Tuple[int, str]]:
    """Return list of bot id and name for all bots."""
    with get_session() as session:
        rows = session.query(Bot.id, Bot.name).order_by(Bot.id).all()
        return [(bot_id, name) for bot_id, name in rows]


def get_bot_token(id: int) -> Optional[str]:
    token = rdb.Bot.get(id)
    if token:
        return token
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return None
        token = bot.get_token()
    rdb.Bot.create(id, token)
    return token


def get_bot_locale(id: int) -> str | None:
    """Return stored locale for a bot."""
    with get_session() as session:
        bot = session.get(Bot, id)
        if not bot:
            return None
        return bot.get_locale()


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
            session.add(
                BotUser(bot_id=bot_id, user_id=user_id, is_owner=True, is_active=True)
            )
        rdb.BotUserStatus.set(bot_id, user_id, True, True)
        rdb.BotOwner.set(bot_id, user_id)
        rdb.BotUsersPage.invalidate(bot_id)


def get_is_bot_owner(bot_id: int, user_id: int) -> bool:
    cached = rdb.BotUserStatus.get(bot_id, user_id)
    if cached is not None:
        return cached["is_owner"]
    with get_session() as session:
        row = (
            session.query(BotUser.is_owner, BotUser.is_active)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .first()
        )
        if row:
            is_owner, is_active = row
            rdb.BotUserStatus.set(bot_id, user_id, is_active, is_owner)
            return bool(is_owner)
        return False


def owner_has_contact(bot_id: int, user_id: int) -> bool:
    """Return True if the owner has provided phone contact."""
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
    cached = rdb.BotOwner.get(bot_id)
    if cached is not None:
        return cached
    with get_session() as session:
        row = (
            session.query(BotUser.user_id)
                   .filter_by(bot_id=bot_id, is_owner=True)
                   .first()
        )
        if row:
            rdb.BotOwner.set(bot_id, row[0])
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

        bu = (
            session.query(BotUser)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .one_or_none()
        )
        if not bu:
            session.add(BotUser(bot_id=bot_id, user_id=user_id, is_active=True))
        else:
            bu.is_active = True
        rdb.BotUserStatus.set(bot_id, user_id, True, False)
        rdb.BotUsersPage.invalidate(bot_id)


def bot_has_user(bot_id: int, user_id: int) -> bool:
    cached = rdb.BotUserStatus.get(bot_id, user_id)
    if cached is not None:
        return True
    with get_session() as session:
        bu = (
            session.query(BotUser.is_active, BotUser.is_owner)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .one_or_none()
        )
        if bu:
            is_active, is_owner = bu
            rdb.BotUserStatus.set(bot_id, user_id, is_active, is_owner)
            return True
        return False


def get_botuser_status(bot_id: int, user_id: int) -> Optional[bool]:
    """Return True/False if user exists, None if not registered"""
    cached = rdb.BotUserStatus.get(bot_id, user_id)
    if cached is not None:
        return cached["is_active"]
    with get_session() as session:
        row = (
            session.query(BotUser.is_active, BotUser.is_owner)
                   .filter_by(bot_id=bot_id, user_id=user_id)
                   .first()
        )
        if row:
            is_active, is_owner = row
            rdb.BotUserStatus.set(bot_id, user_id, is_active, is_owner)
            return is_active
        return None


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
    cached = rdb.BotUsersPage.get(bot_id, page, per_page, search, is_active)
    if cached:
        return cached
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
            raw_phone = user.phone
            if raw_phone:
                try:
                    phone = user.get_phone()
                except InvalidToken as e:
                    phone = raw_phone
            else:
                phone = None

            users.append({
                "id": user.id,
                "name": user.name,
                "surname": user.surname,
                "phone": phone,
                "isOwner": bu.is_owner,
                "status": bu.is_active,
            })
    rdb.BotUsersPage.set(bot_id, page, per_page, search, is_active, users, total)
    return users, total

def get_owner_name(bot_id: int) -> Optional[str]:
    
    with get_session() as session: 
        stmt = (
            select(User.name, User.surname)
            .join(BotUser, BotUser.user_id == User.id)
            .where(BotUser.bot_id == bot_id, BotUser.is_owner.is_(True))
            .limit(1)
        )
        result = session.execute(stmt).first()

        if not result:
            return None

        name, surname = result
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
    rdb.BotUserStatus.delete(bot_id, user_id)
    rdb.BotUsersPage.invalidate(bot_id)
    rdb.BotOwner.delete(bot_id)

def delete_user_by_id(user_id: int) -> None:
    with get_session() as session:
        session.query(User) \
               .filter(User.id == user_id) \
               .delete(synchronize_session=False)
        session.commit()
    # Cannot know all bots, just drop any cached status for this user
    pattern = f"bots:*:users:{user_id}:status"
    for key in rdb.redis_client.scan_iter(pattern):
        rdb.redis_client.delete(key)
    for key in rdb.redis_client.scan_iter(f"bots:*:users-page:*"):
        rdb.redis_client.delete(key)


def delete_botuser(bot_id: int, user_id: int) -> None:
    with get_session() as session:
        session.query(BotUser) \
               .filter(
                   BotUser.bot_id == bot_id,
                   BotUser.user_id == user_id
               ) \
               .delete(synchronize_session=False)
        session.commit()
    rdb.BotUserStatus.delete(bot_id, user_id)
    rdb.BotUsersPage.invalidate(bot_id)
    rdb.BotOwner.delete(bot_id)
