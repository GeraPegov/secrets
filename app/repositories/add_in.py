from datetime import datetime
from redis import RedisError
from fastapi import HTTPException


class AddDatabase():
    def __init__(self, connect):
        self.conn = connect

    def get_key(self, result_encrypt, result_hash, ip_client):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO secrets_users
            (secret, passphrase, ip_client)
            VALUES
            (%s, %s, %s)
            RETURNING id;
            """,
            (result_hash, result_encrypt, ip_client))
        new_key = cursor.fetchone()['id']
        self.conn.commit()
        return new_key


class AddLogger():
    def __init__(self, connect):
        self.conn = connect

    def add_log(self, new_key, ip_client):
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            INSERT INTO logger_secrets
            (secret_key, ip_client, add_secret)
            VALUES
            (%s, %s, %s);
            ''',
            (new_key, ip_client, datetime.now()))
        self.conn.commit()
        return True
    

class CreateCache():
    def __init__(self, connection):
        self.r = connection

    def add_cache(self, key, secret, passphrase, ttl:int = 3600):
        try:
            pipeline = self.r.pipeline()
            pipeline.hset(key, mapping={
                'secret', secret,
                'passphrase', passphrase
            })
            pipeline.expire(key, ttl)
            pipeline.execute()
            return True
        except RedisError as e:
            HTTPException(400, f"Ошибка кеширования: {str(e)}")

