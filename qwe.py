import redis

client = redis.Redis(
    host='localhost',
    port=6379,
    db=0
)
key = 3
secret = 'try'
passphrase = 123

client.flushall()