from fastapi import Depends

from app.repositories.add_in import AddDatabase, AddLogger
from app.services.encrypt import EncryptManager
from app.services.hash import CreateHash
from app.repositories.add_in import CreateCache
from app.core.redis import start_redis
from app.core.database import get_db


def get_hasher():
    return CreateHash()


def get_encrypt():
    return EncryptManager()


def get_db():
    return AddDatabase(get_db)


def get_log():
    return AddLogger(get_db)


def get_cache(connect = Depends(start_redis)):
    return CreateCache(connect)