import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request

from app.dependencies.secret import get_db, get_encrypt, get_hasher, get_log
from app.repositories.task import AddDatabase, AddLogger
from app.services.encrypt import CreateEncrypt
from app.services.get_ip import get_client_ip
from app.services.hash import CreateHash
from app.shemas.schemas import User_add
from log import start_logging

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
        add_log: AddLogger = Depends(get_log)
        ) -> int:

    logger.info('Start /secret')
    try:
        info_of_user = User_add(secret=secret, passphrase=passphrase)
        result_hash = hash.create_hash(info_of_user.passphrase)
        result_encrypt = encrypt.create_encrypt(info_of_user.secret)
        ip_client = get_client_ip(request)
        new_key = add_db.get_key(
            result_encrypt=result_encrypt,
            result_hash=result_hash,
            ip_client=ip_client
        )
        add_log.add_log(ip_client, new_key)
        

            # ПОДКЛЮЧИТЬ РЕДИС 

        return new_key
    except Exception as e:
        raise HTTPException(status_code=404)