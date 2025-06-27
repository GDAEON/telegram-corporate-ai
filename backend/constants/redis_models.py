import json
import redis
from cryptography.fernet import Fernet

from config.settings import FERNET_KEY, REDIS_CONNECTION_URL, REDIS_CACHE_TIME

redis_client = redis.Redis.from_url(REDIS_CONNECTION_URL, decode_responses=True)

cipher = Fernet(FERNET_KEY)

class Bot:
    @staticmethod
    def create(bot_id: int, token: str):
        key = Bot.__redis_key_for_bot_token(bot_id)
        token = cipher.encrypt(token.encode())
        redis_client.set(key, token, ex=int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get(bot_id: int):
        key = Bot.__redis_key_for_bot_token(bot_id)
        token = redis_client.get(key)
        if token:
            return cipher.decrypt(token).decode()
        
        return None

    @staticmethod
    def delete(bot_id: int):
        key = Bot.__redis_key_for_bot_token(bot_id)
        redis_client.delete(key)

    @staticmethod
    def __redis_key_for_bot_token(bot_id: int) -> str:
        return f"bots:{bot_id}:token"


class BotUserStatus:
    """Cache for bot user status and ownership."""

    @staticmethod
    def set(bot_id: int, user_id: int, is_active: bool, is_owner: bool) -> None:
        key = BotUserStatus.__redis_key(bot_id, user_id)
        redis_client.hset(
            key,
            mapping={"is_active": int(is_active), "is_owner": int(is_owner)},
        )
        redis_client.expire(key, int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get(bot_id: int, user_id: int):
        key = BotUserStatus.__redis_key(bot_id, user_id)
        data = redis_client.hgetall(key)
        if not data:
            return None
        return {
            "is_active": bool(int(data.get("is_active", "0"))),
            "is_owner": bool(int(data.get("is_owner", "0"))),
        }

    @staticmethod
    def delete(bot_id: int, user_id: int) -> None:
        key = BotUserStatus.__redis_key(bot_id, user_id)
        redis_client.delete(key)

    @staticmethod
    def __redis_key(bot_id: int, user_id: int) -> str:
        return f"bots:{bot_id}:users:{user_id}:status"


class BotOwner:
    """Cache for bot owner id."""

    @staticmethod
    def set(bot_id: int, user_id: int) -> None:
        key = f"bots:{bot_id}:owner"
        redis_client.set(key, user_id, ex=int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get(bot_id: int):
        key = f"bots:{bot_id}:owner"
        value = redis_client.get(key)
        return int(value) if value is not None else None

    @staticmethod
    def delete(bot_id: int) -> None:
        key = f"bots:{bot_id}:owner"
        redis_client.delete(key)


class BotUsersPage:
    """Cache for paginated users list in admin panel."""

    @staticmethod
    def _key(bot_id: int, page: int, per_page: int, search: str | None, is_active: bool | None) -> str:
        search_part = search or ""
        active_part = "any" if is_active is None else str(int(is_active))
        return f"bots:{bot_id}:users-page:{page}:{per_page}:{search_part}:{active_part}"

    @staticmethod
    def set(
        bot_id: int,
        page: int,
        per_page: int,
        search: str | None,
        is_active: bool | None,
        users: list,
        total: int,
    ) -> None:
        key = BotUsersPage._key(bot_id, page, per_page, search, is_active)
        value = json.dumps({"users": users, "total": total})
        redis_client.set(key, value, ex=int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get(
        bot_id: int,
        page: int,
        per_page: int,
        search: str | None,
        is_active: bool | None,
    ):
        key = BotUsersPage._key(bot_id, page, per_page, search, is_active)
        value = redis_client.get(key)
        if not value:
            return None
        data = json.loads(value)
        return data.get("users"), data.get("total")

    @staticmethod
    def invalidate(bot_id: int) -> None:
        pattern = f"bots:{bot_id}:users-page:*"
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)


class Message:
    """Cache message for sending later."""

    @staticmethod
    def set(bot_id: int, user_id: int, message_id: int, message: str) -> None:
        key = f"bots:{bot_id}:users:{user_id}:messages:{message_id}"
        redis_client.set(key, message, ex=int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get(bot_id: int, user_id: int, message_id: int) -> str:
        key = f"bots:{bot_id}:users:{user_id}:messages:{message_id}"
        value = redis_client.get(key)
        return value if value is not None else None

    @staticmethod
    def delete(bot_id: int, user_id: int, message_id: int) -> None:
        key = f"bots:{bot_id}:users:{user_id}:messages:{message_id}"
        redis_client.delete(key)