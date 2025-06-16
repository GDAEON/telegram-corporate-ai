import json
import redis
from cryptography.fernet import Fernet

from config.settings import FERNET_KEY, REDIS_CONNECTION_URL, REDIS_CACHE_TIME

redis_client = redis.Redis.from_url(REDIS_CONNECTION_URL, decode_responses=True)

cipher = Fernet(FERNET_KEY)

class Bot:
    @staticmethod
    def create(bot_id: int, token: str) -> None:
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
    def delete(bot_id: int) -> None:
        key = Bot.__redis_key_for_bot_token(bot_id)
        redis_client.delete(key)

    @staticmethod
    def set_auth(bot_id: int, name: str, owner_uuid: str, pass_uuid: str, web_url: str) -> None:
        key = Bot.__redis_key_for_bot_auth(bot_id)
        data = {
            "name": name,
            "owner_uuid": owner_uuid,
            "pass_uuid": pass_uuid,
            "web_url": web_url,
        }
        redis_client.set(key, json.dumps(data), ex=int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get_auth(bot_id: int):
        key = Bot.__redis_key_for_bot_auth(bot_id)
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None

    @staticmethod
    def delete_auth(bot_id: int) -> None:
        key = Bot.__redis_key_for_bot_auth(bot_id)
        redis_client.delete(key)

    @staticmethod
    def set_owner_id(bot_id: int, owner_id: int) -> None:
        key = Bot.__redis_key_for_owner_id(bot_id)
        redis_client.set(key, owner_id, ex=int(eval(REDIS_CACHE_TIME)))

    @staticmethod
    def get_owner_id(bot_id: int):
        key = Bot.__redis_key_for_owner_id(bot_id)
        value = redis_client.get(key)
        return int(value) if value is not None else None

    @staticmethod
    def delete_owner_id(bot_id: int) -> None:
        key = Bot.__redis_key_for_owner_id(bot_id)
        redis_client.delete(key)

    @staticmethod
    def exists(bot_id: int) -> bool:
        return bool(redis_client.exists(Bot.__redis_key_for_bot_token(bot_id)) or redis_client.exists(Bot.__redis_key_for_bot_auth(bot_id)))

    @staticmethod
    def __redis_key_for_bot_token(bot_id: int) -> str:
        return f"bots:{bot_id}:token"

    @staticmethod
    def __redis_key_for_bot_auth(bot_id: int) -> str:
        return f"bots:{bot_id}:auth"

    @staticmethod
    def __redis_key_for_owner_id(bot_id: int) -> str:
        return f"bots:{bot_id}:owner"
    