from fastapi import Depends

from app.core.database import get_db
from app.core.redis import start_redis
from app.repositories.add_in import AddDatabase, AddLogger, CreateCache
from app.services.encrypt import EncryptManager
from app.services.hash import CreateHash


def dependencies_hasher():
    return CreateHash()


def dependencies_encrypt():
    return EncryptManager()


def dependencies_db():
    return AddDatabase(get_db)


def dependencies_log():
    return AddLogger(get_db)


def dependencies_cache(connect=Depends(start_redis)):
    return CreateCache(connect)
