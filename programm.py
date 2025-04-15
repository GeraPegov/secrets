from fastapi import FastAPI, HTTPException, Depends, Request, Form, Query
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging 
from log import start_logging
import psycopg2
from database import get_db
from passlib.hash import ldap_pbkdf2_sha256
from cryptography.fernet import Fernet
from schemas import Detail
import toml
import os 
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional

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

def get_client_ip(request: Request) -> str:
    if 'x_forwarded_for' in request.headers:
        return request.headers['x_forwarded_for'].split(",")[0].strip()
    return request.client.host


#шаблон очистки устаревших данных из таблицы
def shemas_cash(conn = Depends(get_db)):
    with conn.cursor() as curs:
        curs.execute('DELETE FROM secrets_users WHERE last_add < NOW() RETURNING id')
        quanity_id = curs.fetchall() 
        if quanity_id:
            logger.info(f'Delete {len(quanity_id)} id(cache)')
        
        conn.commit()

#программа очистки устаревших данных 
def clear_cash():
    scheduler = BackgroundScheduler()
    scheduler.add_job(shemas_cash, 'interval', minutes=5)
    scheduler.start()
    


#Добавление папки с шаблонами html 
templates = Jinja2Templates(directory="templates")

#передача шаблона html 
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):

    return templates.TemplateResponse("form.html", {"request": request})


#обрабатываем информацию ползователя и добавляет в бд 
@app.post('/secret')
async def add_secret(secret: str = Form(...), passphrase: Optional[str] = Form(...), request: Request = None, conn = Depends(get_db)):
    try:
        ip_client = get_client_ip(request)
        logger.info(f'open db for post secret')
        pass_hash = None
        if passphrase:
            pass_hash = ldap_pbkdf2_sha256.hash(passphrase)
        secret_hash = cipher.encrypt(secret.encode()).decode()
        logger.info(f'create secret {secret_hash}')
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO secrets_users (secret, passphrase, ip_client) VALUES (%s, %s, %s) RETURNING id;",
                (secret_hash, pass_hash, ip_client)
            )
            logger.info(f'Add secret_hash in data base')
            new_key = cursor.fetchone()['id']
            conn.commit()
            return new_key
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    

#обработка получения секрета 
@app.get('/showsecret')
async def show_secret(secret_key: int = Query(...), conn = Depends(get_db)):
    try:
        with conn.cursor() as cursor:
            logger.info(f'open db for get secret')
            cursor.execute(
                "SELECT secret, activite_show FROM secrets_users WHERE id = %s and last_add < NOW()", (secret_key,)
            )
            secret_dict = cursor.fetchall()
            logger.info(f'{secret_dict} this is take out database')
            if not secret_dict: 
                logger.warning(f'{secret_key} not found with key')
                raise HTTPException(status_code=404, detail="Секрет не найден")
            if secret_dict[0]['activite_show']:
                logger.warning(f'{secret_dict['activite_show']} secret already show')
                raise HTTPException(status_code=400, detail='this secret already show')
            
            
            
            # if not only_secret or not isinstance(only_secret, str):
            #         logger.info(f'Is not string {only_secret}')
            #         raise HTTPException(status_code=400, detail="Not found key")
            cursor.execute(
                    """
                    UPDATE secrets_users 
                    SET accessed_add = NOW(), activite_show = TRUE
                    WHERE id = %s
                    """,
                    (secret_key,)
                )
            conn.commit()
            only_secret = secret_dict[0]['secret']
            try:
                original_secret =  cipher.decrypt(only_secret).decode()
                logger.info(f'end for show secret')
                
                return original_secret
            
            except Exception as e:
                logger.info(f'warnin for secret {only_secret}')
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка при обработке секрета: {str(e), {only_secret}}"
                )       
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    
#обработка удаления секрета по паролю
@app.post('/delsecret')
async def delsecret(secret_key: int = Form(...), passphrase: str = Form(...), conn = Depends(get_db)) -> Detail:
    try:
        logger.info(f'open db for delete secret')
        with conn.cursor() as cursor:
            cursor.execute('SELECT passphrase FROM secrets_users WHERE id = %s', (secret_key,))
            
            password_hash = cursor.fetchone() 
            if not password_hash:
                logger.info(f'Not found passphrase')
                raise HTTPException(status_code=404, detail="Not found password")
            
            if ldap_pbkdf2_sha256.verify(passphrase, password_hash['passphrase']):
                cursor.execute('DELETE FROM secrets_users WHERE id = %s', (secret_key,))
                conn.commit()
                logger.info(f'delete secret from db')
                return HTTPException(status_code=200, detail='secret is delete')
            raise HTTPException(status_code=403, detail='Invalid passphrase')
    except ResponseValidationError as e:
        logger.info(f'No hash {password_hash['passphrase']} and {passphrase}')
        raise HTTPException(status_code=404, detail='Warning password')
    except Exception as e:
        logger.info(f'WARNING HASH {password_hash}')
        raise HTTPException(status_code=400, detail='Bad Request')