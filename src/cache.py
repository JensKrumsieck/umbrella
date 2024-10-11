import os

import redis


def cache_service() -> redis.Redis:
    redis_url = os.environ.get("KV_URL")
    if redis_url.startswith('redis://'):
        redis_url = 'rediss://' + redis_url[len('redis://'):]
    return redis.from_url(redis_url)


def cache_get(key: str):
    r = cache_service()
    try:
        return r.get(key)
    except:
        print("Vercel KV: Limit reached!")

def cache_get_all(keys: list[str]):
    r = cache_service()
    try:
        return r.mget(keys)
    except:
        print("Vercel KV: Limit reached!")


def cache_set(key: str, value, lifetime: int):
    r = cache_service()
    r.setex(key, lifetime, value)
