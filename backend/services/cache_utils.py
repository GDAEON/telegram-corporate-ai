import json
import functools
from constants.redis_models import redis_client
from config.settings import REDIS_CACHE_TIME


def redis_cache(func):
    """Cache function results in Redis."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key_parts = [func.__name__]
        key_parts.extend(map(str, args))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key = "func-cache:" + ":".join(key_parts)
        cached = redis_client.get(key)
        if cached is not None:
            return json.loads(cached)
        result = func(*args, **kwargs)
        redis_client.set(key, json.dumps(result), ex=int(eval(REDIS_CACHE_TIME)))
        return result

    return wrapper
