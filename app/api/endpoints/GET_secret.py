import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request

from app.dependencies.secret import (dependencies_cache, dependencies_db,
                                     dependencies_encrypt, dependencies_hasher,
                                     dependencies_log)
from app.repositories.add_in import AddDatabase, AddLogger, CreateCache
from app.services.encrypt import EncryptManager
from app.services.get_ip import get_client_ip
from app.services.hash import CreateHash
from app.shemas.schemas import User_add

# from app.services.log import start_logging

router = APIRouter()

# start_logging()
# logger = logging.getLogger(__file__)


@router.post('/secret')
async def add_secret(
        request: Request,
        secret: str = Form(...),
        passphrase: str = Form(...),
        hash: CreateHash = Depends(dependencies_hasher),
        encrypt: EncryptManager = Depends(dependencies_encrypt),
        add_db: AddDatabase = Depends(dependencies_db),
        add_log: AddLogger = Depends(dependencies_log),
        add_cache: CreateCache = Depends(dependencies_cache)
        ) -> int:
    try:
        info_of_user = User_add(secret=secret, passphrase=passphrase)
        passphrase_hash = hash.create_hash(info_of_user.passphrase)
        secret_encrypt = encrypt.create_encrypt(info_of_user.secret)
        ip_client = get_client_ip(request)

        new_key = add_db.get_key(
            result_encrypt=secret_encrypt,
            result_hash=passphrase_hash,
            ip_client=ip_client
        )

        add_cache.create_cache(
            key=new_key,
            passphrase=passphrase_hash,
            secret=secret_encrypt
        )
        return new_key
    except Exception as e:
        raise HTTPException(404, f'Непредвиденная ошибка: {str(e)}')
