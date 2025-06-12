from fastapi import Depends

from app.repositories.delete import DeleteSecretCACHE, DeleteSecretDB
from app.core.database import get_db
from app.core.redis import start_redis

def del_secret_db(connection = Depends(get_db)):
    return DeleteSecretDB(connection)

def del_secret_cache(connection = Depends(start_redis)):
    return  DeleteSecretCACHE(connection)