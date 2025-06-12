import redis


def start_redis():
    r = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    try:
        yield r
    finally:
        r.close()
