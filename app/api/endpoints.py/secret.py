import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request

from app.dependencies.secret import get_db, get_encrypt, get_hasher, get_log, get_cache
from app.repositories.add_in import AddDatabase, AddLogger
from app.services.encrypt import CreateEncrypt
from app.services.get_ip import get_client_ip
from app.services.hash import CreateHash
from app.shemas.schemas import User_add
from log import start_logging
from app.services.cache import CreateCache



router = APIRouter()

start_logging()
logger = logging.getLogger(__file__)


@router.post('/secret')
async def add_secret(
        request: Request,
        secret: str = Form(...),
        passphrase: str = Form(...),
        hash: CreateHash = Depends(get_hasher),
        encrypt: CreateEncrypt = Depends(get_encrypt),
        add_db: AddDatabase = Depends(get_db),
        add_log: AddLogger = Depends(get_log),
        add_cache: CreateCache = Depends(get_cache)
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
        add_log.add_log(ip_client, new_key)
        add_cache.add_cache(
            key=new_key,
            passphrase=passphrase_hash,
            secret=secret_encrypt
        )
        return new_key
    except Exception as e:
        raise HTTPException(status_code=404)