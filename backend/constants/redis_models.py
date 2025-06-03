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
    