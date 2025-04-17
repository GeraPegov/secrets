from fastapi import FastAPI, HTTPException, Depends, Request, Form, Query
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging 
from log import start_logging
import psycopg2
from database import get_db, start_table
from passlib.hash import ldap_pbkdf2_sha256
from cryptography.fernet import Fernet
from schemas import Detail
import toml
import os 
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
import time
from datetime import datetime

#инициализация логирования
start_logging()
logger =logging.getLogger(__name__)

#открытие конфига для ключа шифрования 
config_path = os.environ.get('CONFIG_PATH', 'config.toml')
with open(config_path) as f:  
    config = toml.load(f)
encryption_key = os.environ.get('ENCRIPTION_KEY', config['KEY'])
cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

#инициализация FastAPI
app = FastAPI(
    title='Одноразовые секреты',
    description='Приложение для хранения секретов',
    version='1.0.0'
)

#чтот когда заходит за прокси надо узнать 
def get_client_ip(request: Request) -> str:
    if 'x_forwarded_for' in request.headers:
        return request.headers['x_forwarded_for'].split(",")[0].strip()
    return request.client.host

#шаблон очистки устаревших данных из таблицы
cache = {} 

#Добавление папки с шаблонами html 
templates = Jinja2Templates(directory="templates")

scheduler = BackgroundScheduler()

def shemas_cash():
    logger.info(f'SHEMAS')
    try:
        with start_table() as conn:
            with conn.cursor() as curs:
                curs.execute('DELETE FROM secrets_users WHERE last_add < NOW() RETURNING id')
                logger.info(f'clear db')
                quanity_id = curs.fetchall() 
                logger.info(f'{quanity_id} quanity id ')
                conn.commit()
                if quanity_id:
                    logger.info(f'Delete {len(quanity_id)} id(cache)')
                    for i in quanity_id:
                        if i in cache:
                            del cache[i]        
    except Exception as e:
        raise HTTPException(status_code=404)

# программа очистки устаревших данных 
def clear_cash():
    logger.info(f'CASH')
    scheduler.add_job(shemas_cash, 'interval', minutes=5)
    scheduler.start()
    logger.info(f'end clear')
    
@app.on_event('startup')
async def delcache():
    logger.info('start delcache')
    clear_cash()
    logger.info(f'CLEANUP CONNECTION PLAN ')


#передача шаблона html 
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

#обрабатываем информацию ползователя и добавляет в бд 
@app.post('/secret')
async def add_secret(secret: str = Form(...), passphrase: Optional[str] = Form(...), request: Request = None, conn = Depends(get_db)):
    try:
        #шифрование данных
        ip_client = get_client_ip(request)
        logger.info(f'open db for post secret')
        pass_hash = ldap_pbkdf2_sha256.hash(passphrase)
        secret_hash = cipher.encrypt(secret.encode()).decode()
        #добавление данных
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO secrets_users (secret, passphrase, ip_client) VALUES (%s, %s, %s) RETURNING id;",
                (secret_hash, pass_hash, ip_client)
            )
            logger.info(f'Add secret_hash in data base')
            new_key = cursor.fetchone()['id']
            #логирование в базу данных
            cursor.execute(
                '''
                INSERT INTO logger_secrets (secret_key, ip_user, add_secret) VALUES (%s, %s, %s);
                ''',
                (new_key, ip_client, datetime.now())
            )
            conn.commit()
            #кеширование занесенных данных
            cache[new_key] = {"secret": secret_hash, 'time': time.time()+600}
            logger.info(f'cache added')
            return new_key
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    

#обработка получения секрета 
@app.get('/showsecret')
async def show_secret(secret_key: int = Query(...), conn = Depends(get_db), request: Request = None):
    try:
        ip_client = get_client_ip(request)
        secret = None
        #проверка секрета в кеше и апдейт таблицы
        if secret_key in cache and cache[secret_key]['time'] > time.time():
            secret = cache[secret_key]['secret']
            logger.info(f'{secret} cahce get')
            del cache[secret_key]
            with conn.cursor() as cursor:     
                cursor.execute(
                        """
                        UPDATE secrets_users 
                        SET accessed_add = NOW(), activite_show = TRUE
                        WHERE id = %s
                        """,
                        (secret_key,)
                    )
                #логирование в базу данных
                cursor.execute(
                        '''
                        INSERT INTO logger_secrets (secret_key, ip_user, first_reading) VALUES (%s, %s, %s);
                        ''',
                        (secret_key, ip_client, datetime.now())
                    )
                conn.commit()
        #проверка таблицы если нет в кеше и апдейт     
        else:
            with conn.cursor() as cursor:
                logger.info(f'open db for get secret')
                cursor.execute(
                    "SELECT secret, activite_show, first_add FROM secrets_users WHERE id = %s and last_add > NOW()", (secret_key,)
                )
                secret_dict = cursor.fetchall()
                logger.info(f'{secret_dict} this is take out database')
                #проверка если нет секрета
                if not secret_dict: 
                    logger.warning(f'{secret_key} not found with key')
                    raise HTTPException(status_code=404, detail="Секрет не найден")
                #проверка если значения activite_show True(просмотрено)
                if secret_dict[0]['activite_show']:
                    logger.warning(f'{secret_dict[0]['activite_show']} secret already show')
                    raise HTTPException(status_code=400, detail='this secret already show')  
                cursor.execute(
                        """
                        UPDATE secrets_users 
                        SET accessed_add = NOW(), activite_show = TRUE
                        WHERE id = %s
                        """,
                        (secret_key,)
                    )
                #логирование в базу данных
                cursor.execute(
                        '''
                        INSERT INTO logger_secrets (secret_key, ip_user, first_reading) VALUES (%s, %s, %s);
                        ''',
                        (secret_key, ip_client, datetime.now())
                    )
                conn.commit()
        #проверка откуда взяли секрет(таблица или кеш)
        if not secret:
            secret = secret_dict[0]['secret']
        #попытка расшифровки
        try:
            original_secret =  cipher.decrypt(secret).decode()
            logger.info(f'end for show secret')
            return original_secret
        
        except Exception as e:
            logger.info(f'warnin for secret {secret}')
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка при обработке секрета: {str(e), {secret}}"
            )       
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    
#обработка удаления секрета по паролю
@app.post('/delsecret')
async def delsecret(secret_key: int = Form(...), passphrase: str = Form(...), conn = Depends(get_db), request: Request = None) -> Detail:
    try:
        ip_client = get_client_ip(request)
        with conn.cursor() as cursor:
            logger.info('open db for delete')
            cursor.execute('SELECT passphrase FROM secrets_users WHERE id = %s', (secret_key,))
            password_hash = cursor.fetchone() 
            #проверка наличия пароля
            if not password_hash:
                logger.info(f'Not found passphrase')
                raise HTTPException(status_code=404, detail="Not found password")
            #проверка верности пароля
            if not ldap_pbkdf2_sha256.verify(passphrase, password_hash['passphrase']):
                logger.info('password is not verify')
                raise HTTPException(status_code=403, detail='Invalid passphrase')
            #удаление поля из таблицы 
            cursor.execute('DELETE FROM secrets_users WHERE id = %s', (secret_key,))
            cursor.execute(
                        '''
                        INSERT INTO logger_secrets (secret_key, ip_user, delete_secret) VALUES (%s, %s, %s);
                        ''',
                        (secret_key, ip_client, datetime.now())
                    )
            conn.commit()
            logger.info(f'delete secret from db')
            return HTTPException(status_code=200, detail='secret is delete')
            
    except ResponseValidationError as e:
        logger.info(f'No hash {password_hash['passphrase']} and {passphrase}')
        raise HTTPException(status_code=404, detail='Warning password')
    except Exception as e:
        logger.info(f'WARNING HASH')
        raise HTTPException(status_code=400, detail='Bad Request')
    
