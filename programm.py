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



start_logging()
logger =logging.getLogger(__name__)
with open("config.toml") as f:  
    data = toml.load(f)
cipher = Fernet(data['KEY'])
app = FastAPI()
templates = Jinja2Templates(directory="templates")

#передача шаблона html 
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


#Form() помогает FastAPI найти данные необходимые, преобразовать в пайтон типы, проверяет валидацию 
@app.post('/secret')
async def add_secret(secret: str = Form(...), passphrase: str = Form(...), conn = Depends(get_db)):
    try:
        
        pass_hash = ldap_pbkdf2_sha256.hash(passphrase)
        secret_hash = cipher.encrypt(secret.encode()).decode()
        logger.info(f'create secret {secret_hash}')
        # pwd_context.verify(passphrase, pass_hash)
        logger.info(f'add {secret} it is {secret_hash}')
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO secrets_users (secret, passphrase) VALUES (%s, %s) RETURNING id;",
                (secret_hash, pass_hash)
            )
            
            new_key = cursor.fetchone()
            conn.commit()
            return new_key
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    


@app.get('/showsecret')
async def show_secret(secret_key: int = Query(...), conn = Depends(get_db)):
    try:
        with conn.cursor() as cursor:
            logger.info(f'open bd')
            cursor.execute(
                "SELECT secret FROM secrets_users WHERE id = %s", (secret_key,)
            )
            new_item = cursor.fetchone()
            cursor.execute('DELETE FROM secrets_users WHERE id = %s', (secret_key,))
            conn.commit()
            logger.info(f'{new_item} this is take out bd')
            if not new_item:  # Проверяем, есть ли данные
                logger.warning(f'{secret_key} not found with key')
                raise HTTPException(status_code=404, detail="Секрет не найден")
            
            key = new_item['secret']
            logger.info(f'{key} this is take KEY, {type(key)} this is type KEY')
            try:
                if not key or not isinstance(key, str):
                    logger.info(f' not key {key}')
                    raise HTTPException(status_code=400, detail="i dont know why")
                value =  cipher.decrypt(key).decode()
                logger.info(f'{value} this is last version')
                
                return value
            except Exception as e:
                logger.info(f'warnin for secret {key}')
                raise HTTPException(
                    status_code=400,
                    detail=f"Ошибка при обработке секрета: {str(e), {key}}"
                )       
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    
    
@app.post('/delsecret')
async def delsecret(secret_key: int = Form(...), passphrase: str = Form(...), conn = Depends(get_db)) -> Detail:
    try:
        logger.info(f'OPEN BD DELETE')
        with conn.cursor() as cursor:
            cursor.execute('SELECT passphrase FROM secrets_users WHERE id = %s', (secret_key,))
            
            password_hash = cursor.fetchone() 
            if not password_hash:
                logger.info(f'Not found passphrase')
                raise HTTPException(status_code=404, detail="Not found password")

            if ldap_pbkdf2_sha256.verify(passphrase, password_hash['passphrase']):
                cursor.execute('DELETE FROM secrets_users WHERE id = %s', (secret_key,))
                conn.commit()
                return HTTPException(status_code=200, detail='password is delete')
            raise HTTPException(status_code=403, detail='Invalid passphrase')
    except ResponseValidationError as e:
        logger.info(f'No hash {password_hash['passphrase']} and {passphrase}')
        raise HTTPException(status_code=404, detail='Warning password')
    except Exception as e:
        logger.info(f'WARNING HASH {password_hash}')
        raise HTTPException(status_code=400, detail='Bad Request')