from fastapi import APIRouter, Depends, Form, Request

from app.dependencies.secret import get_db, get_encrypt, get_hasher, get_log
from app.services.encrypt import CreateEncrypt
from app.services.hash import CreateHash

router = APIRouter()

@router.post('/secret')
async def add_secret(
    request: Request,
    secret: str = Form(...),
    passphrase: str = Form(...),
    create_hash: CreateHash = Depends(get_hasher),
    create_encrypt: CreateEncrypt = Depends(get_encrypt),
    add_db: AddDatabase = Depends(get_db),
    add_log: AddLogger = Depends(get_log)
    ) -> int:
    """
    Обработка данных пользователя. HTML сохраняет данные secret и passphrase и вынимает их из запроса.
    Хэшируем пароль, шифруем данные и заносим в базу данных и кэш, присваивая им секретный ключ(id), который
    отправляется пользователю. Все данные пользователя логируются в отдельную таблицу(секретный ключ, ip, время добавления)
    """
    logger.info('Start /secret')
    try:
        # Так как вынимаем из формы значения мы отдельно добавляем их в класс Pydantic
        info_of_user = User_add(secret=secret, passphrase=passphrase)
        # ХЭширование пароля и шифрование данных
        result_hash = create_hash.create_hash(info_of_user.passphrase)
        result_encrypt = create_encrypt.create_encrypt(info_of_user.secret)
        logger.info(f'{result_encrypt, result_hash}, result')
        # находим айпи клиента
        ip_client = get_client_ip(request)
        logger.info(f'{ip_client}, ip_client')
        # Добавляем секрет(secret), пароль(passphrase), айпи клиента(ip_client) и выдаем секретный ключ(id)
        new_key = add_db.get_key(
            result_encrypt=result_encrypt, 
            result_hash=result_hash, 
            ip_client=ip_client
        )
        db_log = add_log.add_log(
            ip_client=ip_client,
            new_key=new_key
        )
        

            # ПОДКЛЮЧИТЬ РЕДИС 

        return new_key
    except Exception as e:
        raise HTTPException(status_code=404)