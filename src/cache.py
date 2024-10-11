import os

import redis


def cache_service() -> redis.Redis:
    redis_url = os.environ.get("KV_URL")
    if redis_url.startswith('redis://'):
        redis_url = 'rediss://' + redis_url[len('redis://'):]
    return redis.from_url(redis_url)
