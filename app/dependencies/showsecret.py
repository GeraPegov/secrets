from fastapi import Depends

from app.repositories.get_off import ShowSecretDB, ShowSecretCACHE
from app.core.database import get_db
from app.core.redis import start_redis

def get_secret_db(connection = Depends(get_db)):
    return ShowSecretDB(connection)

def get_secret_cache(connection = Depends(start_redis)):
    return  ShowSecretCACHE(connection)