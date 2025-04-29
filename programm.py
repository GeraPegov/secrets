from fastapi import FastAPI, HTTPException, Depends, Request, Form, Query
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging 
from log import start_logging
import psycopg2
from database import get_db, start_table, init_db
from passlib.hash import ldap_pbkdf2_sha256
from cryptography.fernet import Fernet
from schemas import Detail, User_add
import toml
import os 
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime

#Инициализация логирования
start_logging()
logger =logging.getLogger(__name__)

#Открытие конфига для ключа шифрования 
config_path = os.environ.get('CONFIG_PATH', 'config.toml')
with open(config_path) as f:  
    config = toml.load(f)
encryption_key = os.environ.get('ENCRIPTION_KEY', config['KEY'])
cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

#Сохранение IP клиента 
def get_client_ip(request: Request) -> str:
    if 'x_forwarded_for' in request.headers:
        return request.headers['x_forwarded_for'].split(",")[0].strip()
    return request.client.host

#Хранение кэша
cache = {} 

#Добавление папки с шаблонами html 
templates = Jinja2Templates(directory="templates")

#Экземпляр класса планировщика задач
scheduler = BackgroundScheduler()

def shemas_cash():
    """
    Инициализация очистки устаревших данных в таблице и очистка кэша. 
    Очистка производится каждый час в соответствии с планировщиком clear_cash()
    """
    logger.info(f'Start shemas_cash')
    try:
        with start_table() as conn:
            with conn.cursor() as curs:
                logger.info(f'Open db in shemas_cash()')
                curs.execute('DELETE FROM secrets_users WHERE last_add < NOW() RETURNING id')
                quanity_id = curs.fetchall() 
                conn.commit()
                if quanity_id:
                    logger.info(f'Delete {len(quanity_id)} id(cache)')
                    for i in quanity_id:
                        if i in cache:
                            del cache[i]        
    except Exception as e:
        raise HTTPException(status_code=404)

def clear_cash():
    logger.info(f'Start clear_cash')
    scheduler.add_job(shemas_cash, 'interval', minutes=60)
    scheduler.start()
    logger.info(f'End clear_cash')


def startup():
    init_db()
    logger.info('Start lifespan')
    clear_cash()

#Инициализация FastAPI
app = FastAPI(
    title='Одноразовые секреты',
    description='Приложение для хранения секретов',
    version='1.0.0',
)
app.add_event_handler('startup', startup)
#Передача шаблона html 
@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post('/secret')
def add_secret(
    secret: str = Form(...), 
    passphrase: str = Form(...), 
    request: Request = None, 
    conn = Depends(get_db)
    ):
    """
    Обработка данных пользователя. HTML сохраняет данные secret и passphrase и вынимает их из запроса.
    Хэшируем пароль, шифруем данные и заносим в базу данных и кэш, присваивая им секретный ключ(id), который
    отправляется пользователю. Все данные пользователя логируются в отдельную таблицу(секретный ключ, ip, время добавления)
    """
    logger.info('Start /secret')
    try:
        #Так как вынимаем из формы значения мы отдельно добавляем их в класс Pydantic
        User_add(secret=secret, passphrase=passphrase)
        ip_client = get_client_ip(request)
        #Пароль хэшируем без возможности посмотреть его значение
        pass_hash = ldap_pbkdf2_sha256.hash(passphrase)
        #Секрет шифруем с помощью нашего кода шифрования, чтобы потом расшифровать и выдать по запросу
        secret_hash = cipher.encrypt(secret.encode()).decode()
        logger.info(f'Open db for add secret and passphrase in table')
        #Добавляем секрет(secret), пароль(passphrase), айпи клиента(ip_client) и выдаем секретный ключ(id)
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO secrets_users 
                (secret, passphrase, ip_client) 
                VALUES 
                (%s, %s, %s) 
                RETURNING id;
                """,
                (secret_hash, pass_hash, ip_client))
            logger.info(f'Add secret and passphrase in db')
            #Добавленным данным присваиваем секретный ключ(id)
            new_key = cursor.fetchone()['id']
            logger.info(f'{new_key} new key')
            #Логирование секретного ключа(secret_key), айпи клиента(id_user), время добавления(add_secret)
            cursor.execute(
                '''
                INSERT INTO logger_secrets 
                (secret_key, ip_client, add_secret) 
                VALUES 
                (%s, %s, %s);
                ''',
                (new_key, ip_client, datetime.now()))
            conn.commit()
            #Кеширование секретного ключа(secret) и времени окончания действия(time), которые пользователь может получить в течении 10 минут
            cache[new_key] = {"secret": secret_hash, 'time': time.time()+600}
            logger.info(f'Added secret and time in cache')
            return new_key
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)

@app.get('/showsecret')
def show_secret(
    secret_key: int = Query(...), 
    conn = Depends(get_db), 
    request: Request = None
    ):
    """
    Выдача секрета по секретному ключу и паролю. Сначала проверяется доступен ли
    секрет в кеше(отправляем пользователю и удаляем из кеша), обновляем базу данных(секрет просмотрен),
    и логируем в отдельную таблицу.
    Если в кеше секрета нет(вышло 10 минут) - открываем бд, ищем, при значении last_add > NOW() (если 
    не вышло время хранения секрета) и activite_show = False (секрет еще не просмотрен), выдаем секрет, обновляем бд
    (секрет просмотрен(activite_show = True)) и логируем действия в отдельную таблицу.

    """
    logger.info(f'Start /showsecret')
    try:
        # Secret(secret_key=secret_key)
        ip_client = get_client_ip(request)
        #secret присваивает значение либо из кэша, либо из таблицы
        secret = None
        #Проверка секрета в кеше
        if secret_key in cache and cache[secret_key]['time'] > time.time():
            secret = cache[secret_key]['secret']
            del cache[secret_key]
            logger.info(f'Secret show from cache. Update table')
            
            with conn.cursor() as cursor:    
                #Обновление времени просмотра(show_secret)
                #Статуса секрета(просмотрено(True)) 
                cursor.execute(
                        """
                        UPDATE secrets_users 
                        SET show_secret = NOW(), activite_show = TRUE
                        WHERE id = %s
                        """,
                        (secret_key,)
                    )
                #Логирование секрета(secret_key)
                #Айпи пользователя(ip_user)
                #Время просмотра(time_reading)
                logger.info(f'Update logger-table after update table after show secret from CACHE')
                cursor.execute(
                        '''
                        INSERT INTO logger_secrets 
                        (secret_key, ip_user, time_reading) 
                        VALUES 
                        (%s, %s, %s);
                        ''',
                        (secret_key, ip_client, datetime.now())
                    )
                conn.commit()
        #Проверка в таблице секрета если нет в кеше  
        else:
            with conn.cursor() as cursor:
                #Вынимаем секрет(secret)
                #Cтатус секрета(activite_show(True or False))
                #Проверяем просрочку (last_add > NOW())
                logger.info(f'Open db for get secret')
                cursor.execute(
                    """
                    SELECT secret, activity_status
                    FROM secrets_users 
                    WHERE id = %s and last_add > NOW()
                    """, 
                    (secret_key,))
                secret_dict = cursor.fetchall()
                #Проверка если нет секрета
                if not secret_dict: 
                    logger.warning(f'{secret_key} not found with key')
                    raise HTTPException(status_code=404, detail="Секрет не найден")
                #Проверка если значения activity_status=True(просмотрено)
                if secret_dict[0]['activity_status']:
                    raise HTTPException(status_code=400, detail='Секрет уже просмотрели')  
                #show_secret = NOW() (время просмотра секрета)
                #activite_shpw=True(просмотрено)
                logger.info(f'Secret show from table. Update table')
                cursor.execute(
                        """
                        UPDATE secrets_users 
                        SET show_secret = NOW(), activity_status = TRUE
                        WHERE id = %s
                        """,
                        (secret_key,))
                #Логирование секретного ключа(secret_key)
                #Айпи пользователя(ip_user) 
                #Времени просмотра(time_reading)
                logger.info(f'Update logger-table after update table after show secret from TABLE')
                cursor.execute(
                        '''
                        INSERT INTO logger_secrets 
                        (secret_key, ip_client, time_reading) 
                        VALUES 
                        (%s, %s, %s);
                        ''',
                        (secret_key, ip_client, datetime.now()))
                conn.commit()
        #Проверка если не нашли секрет
        if not secret:
            secret = secret_dict[0]['secret']
        #Расшифровка секрета
        try:
            #secret присвоил значение секрета из кеша или таблицы
            original_secret =  cipher.decrypt(secret).decode()
            logger.info(f'decrupt secret success')
            return original_secret
        except Exception as e:
            logger.info(f'decryp secret false')
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка при обработке секрета: {str(e), {secret}}"
            )       
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    except ValueError as e:
        raise HTTPException(status_code=400, detail='wrond input')
    
#обработка удаления секрета по паролю
@app.post('/delsecret')
def delsecret(
    secret_key: int = Form(...), 
    passphrase: str = Form(...), 
    conn = Depends(get_db), 
    request: Request = None
    ) -> Detail:
    logger.info(f'Start /delsecret')
    """
    По секретному ключу и паролю удаление секрета из базы данных. 
    """
    try:
        ip_client = get_client_ip(request)
        #Вынимаем пароль(passphrase) по секретному ключу(id)
        with conn.cursor() as cursor:
            logger.info('open db for delete')
            cursor.execute(
                '''
                SELECT passphrase 
                FROM secrets_users 
                WHERE id = %s
                ''', 
                (secret_key,))
            password_hash = cursor.fetchone() 
            #Проверка наличия пароля
            if not password_hash:
                logger.info(f'Not found passphrase')
                raise HTTPException(status_code=404, detail="Нет пароля или записи в базе данных")
            #Проверка верности пароля 
            if not ldap_pbkdf2_sha256.verify(passphrase, password_hash['passphrase']):
                logger.info('password is not verify')
                raise HTTPException(status_code=403, detail='Неверный пароль')
            #Удаление поля из таблицы по значению секретного ключа(id)
            cursor.execute(
                '''
                DELETE FROM secrets_users 
                WHERE id = %s
                ''',
                (secret_key,))
            #Логирование секретного ключа, айпи, и времени удаления секрета(delete_secret)
            cursor.execute(
                '''
                INSERT INTO logger_secrets 
                (secret_key, ip_client, delete_secret) 
                VALUES 
                (%s, %s, %s);
                ''',
                (secret_key, ip_client, datetime.now()))
            conn.commit()
            logger.info(f'Delete secret from db')
            return HTTPException(status_code=200, detail='Секрет удален')
    except ResponseValidationError as e:
        logger.info(f'No hash {password_hash['passphrase']} and {passphrase}')
        raise HTTPException(status_code=404, detail='Warning password')
    except Exception as e:
        logger.info(f'WARNING HASH')
        raise HTTPException(status_code=400, detail='Bad Request')
    
