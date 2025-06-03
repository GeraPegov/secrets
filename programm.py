import os 

from fastapi import FastAPI, HTTPException, Depends, Request, Form, Query, Response
from fastapi.exceptions import ResponseValidationError, ValidationException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging 
import psycopg2
from passlib.hash import ldap_pbkdf2_sha256

from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime

from log import start_logging
from schemas import Detail, User_add, Secret, Delete
from main.encrypt_info import CreateHash, CreateEncrypt
from database.task import AddDatabase, AddLogger
from main.dependencies import get_encrypt, get_hasher, get_db, get_log

#Инициализация логирования
start_logging()
logger =logging.getLogger(__name__)

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

# def shemas_cash():
#     """
#     Инициализация очистки устаревших данных в таблице и очистка кэша. 
#     Очистка производится каждый час в соответствии с планировщиком clear_cash()
#     """
#     logger.info(f'Start shemas_cash')
#     try:
#         with start_table() as conn:
#             with conn.cursor() as curs:
#                 logger.info(f'Open db in shemas_cash()')
#                 curs.execute('DELETE FROM secrets_users WHERE last_add < NOW() RETURNING id')
#                 quanity_id = curs.fetchall() 
#                 conn.commit()
#                 if quanity_id:
#                     logger.info(f'Delete {len(quanity_id)} id(cache)')
#                     for i in quanity_id:
#                         if i in cache:
#                             del cache[i]        
#     except Exception as e:
#         raise HTTPException(status_code=404)

# def clear_cash():
#     logger.info(f'Start clear_cash')
#     scheduler.add_job(shemas_cash, 'interval', minutes=60)
#     scheduler.start()
#     logger.info(f'End clear_cash')

# def startup():
#     init_db()
#     logger.info('Start lifespan')
#     clear_cash()
#Инициализация FastAPI
app = FastAPI(
    title='Одноразовые секреты',
    description='Приложение для хранения секретов',
    version='1.0.0',
)
# Функция для добавления заголовков запрета кеширования
def add_no_cache_headers(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
# app.add_event_handler('startup', startup)
#Передача шаблона html 
@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post('/secret')
async def add_secret(
    secret: str = Form(...), 
    passphrase: str = Form(...), 
    request: Request = None, 
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
        #Так как вынимаем из формы значения мы отдельно добавляем их в класс Pydantic
        info_of_user = User_add(secret=secret, passphrase=passphrase)
        #ХЭширование пароля и шифрование данных
        result_hash = create_hash.create_hash(info_of_user.passphrase)
        result_encrypt = create_encrypt.create_encrypt(info_of_user.secret)
        logger.info(f'{result_encrypt, result_hash}, result')
        #находим айпи клиента
        ip_client = get_client_ip(request)
        logger.info(f'{ip_client}, ip_client')
        #Добавляем секрет(secret), пароль(passphrase), айпи клиента(ip_client) и выдаем секретный ключ(id)
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

# @app.get('/showsecret')
# async def show_secret(
#     secret_key: int = Query(...), 
#     conn = Depends(get_db), 
#     request: Request = None
#     ) -> str:
#     """
#     Выдача секрета по секретному ключу и паролю. Сначала проверяется доступен ли
#     секрет в кеше(отправляем пользователю и удаляем из кеша), обновляем базу данных(секрет просмотрен),
#     и логируем в отдельную таблицу.
#     Если в кеше секрета нет(вышло 10 минут) - открываем бд, ищем, при значении last_add > NOW() (если 
#     не вышло время хранения секрета) и activite_show = False (секрет еще не просмотрен), выдаем секрет, обновляем бд
#     (секрет просмотрен(activite_show = True)) и логируем действия в отдельную таблицу.

#     """
#     logger.info(f'Start /showsecret')
#     try:
#         key = Secret(secret_key=secret_key)
#         ip_client = get_client_ip(request)
#         # logger.info(key.secret_key)
#         #secret присваивает значение либо из кеша, либо из таблицы
#         secret = None
#         #Проверка секрета в кеше
#         if key.secret_key in cache and cache[key.secret_key]['time'] > time.time():
#             secret = cache[key.secret_key]['secret']
#             del cache[key.secret_key]
#             logger.info(f'Secret show from cache. Update table')
#             try:
#                 with conn.cursor() as cursor:    
#                     #Обновление времени просмотра(show_secret)
#                     #Статуса секрета(просмотрено(True)) 
#                     cursor.execute(
#                             """
#                             UPDATE secrets_users 
#                             SET show_secret = NOW(), activity_status = TRUE
#                             WHERE id = %s
#                             """,
#                             (key.secret_key,)
#                         )
#                     #Логирование секрета(secret_key)
#                     #Айпи пользователя(ip_user)
#                     #Время просмотра(time_reading)
#                     logger.info(f'Update logger-table after update table after show secret from CACHE')
#                     cursor.execute(
#                             '''
#                             INSERT INTO logger_secrets 
#                             (secret_key, ip_user, time_reading) 
#                             VALUES 
#                             (%s, %s, %s);
#                             ''',
#                             (key.secret_key, ip_client, datetime.now())
#                         )
#                     conn.commit()
#             except psycopg2.Error as e:
#                 conn.rollback()
#                 raise HTTPException(status_code=400, detail="Ошибка базы данных")
#         #Проверка в таблице секрета если нет в кеше  
#         else:
#             try:
#                 with conn.cursor() as cursor:
#                     #Вынимаем секрет(secret)
#                     #Cтатус секрета(activite_show(True or False))
#                     #Проверяем просрочку (last_add > NOW())
#                     logger.info(f'Open db for get secret')
#                     cursor.execute(
#                         """
#                         SELECT secret, activity_status
#                         FROM secrets_users 
#                         WHERE id = %s and last_add > NOW()
#                         """, 
#                         (key.secret_key,))
#                     secret_dict = cursor.fetchall()
#                     #Проверка если нет секрета
#                     if not secret_dict: 
#                         logger.warning(f'{key.secret_key} not found key')
#                         raise HTTPException(status_code=404, detail="Секрет не найден")
#                     #Проверка если значения activity_status=True(просмотрено)
#                     if secret_dict[0]['activity_status']:
#                         raise HTTPException(status_code=400, detail='Секрет уже просмотрели')  
#                     #show_secret = NOW() (время просмотра секрета)
#                     #activite_shpw=True(просмотрено)
#                     logger.info(f'Secret show from table. Update table')
#                     cursor.execute(
#                             """
#                             UPDATE secrets_users 
#                             SET show_secret = NOW(), activity_status = TRUE
#                             WHERE id = %s
#                             """,
#                             (key.secret_key,))
#                     #Логирование секретного ключа(secret_key)
#                     #Айпи пользователя(ip_user) 
#                     #Времени просмотра(time_reading)
#                     logger.info(f'Update logger-table after update table after show secret from TABLE')
#                     cursor.execute(
#                             '''
#                             INSERT INTO logger_secrets 
#                             (secret_key, ip_client, time_reading) 
#                             VALUES 
#                             (%s, %s, %s);
#                             ''',
#                             (key.secret_key, ip_client, datetime.now()))
#                     conn.commit()
#             except psycopg2.Error as e:
#                 conn.rollback()
#                 raise HTTPException(status_code=400, detail="Ошибка базы данных")
#         #Проверка если секрета нет в кэше
#         if not secret:
#             secret = secret_dict[0]['secret']
#         #Расшифровка секрета
#         try:
#             #secret присвоил значение секрета из кеша или таблицы
#             original_secret =  cipher.decrypt(secret).decode()
#             logger.info(f'Decrupt secret success')
#             response = JSONResponse(content={'secret':original_secret})
#             return add_no_cache_headers(response)
#         except TypeError as e:
#             logger.info(f'Type secret is not bytes')
#             raise HTTPException(detail='Ошибка сервера')
#         except InvalidToken as e:
#             logger.info(f'Not key of decrypt')
#             raise HTTPException(status_code=404, detail='Ошибка данных')
#         except Exception as e:
#             logger.info(f'Decrypt secret false')
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Ошибка при обработке секрета: {str(e), {secret}}"
#             )          
#     except ValidationException as e:
#         raise HTTPException(status_code=422, detail='Некорректный ввод')
#     except Exception as e:
#         raise HTTPException(status_code=400, detail='Неизвестная ошибка')
    
# #Обработка удаления секрета по паролю
# @app.post('/delsecret')
# async def delsecret(
#     secret_key: int = Form(...), 
#     passphrase: str = Form(...), 
#     conn = Depends(get_db), 
#     request: Request = None
#     ) -> Detail:
#     logger.info(f'Start /delsecret')
#     """
#     По секретному ключу и паролю удаление секрета из базы данных. 
#     """
#     try:
#         delete = Delete(secret_key=secret_key, passphrase=passphrase)
#         ip_client = get_client_ip(request)
#         #Вынимаем пароль(passphrase) по секретному ключу(id)
#         with conn.cursor() as cursor:
#             logger.info('open db for delete')
#             cursor.execute(
#                 '''
#                 SELECT passphrase 
#                 FROM secrets_users 
#                 WHERE id = %s
#                 ''', 
#                 (delete.secret_key,))
#             password_hash = cursor.fetchone() 
#             #Проверка наличия пароля
#             if not password_hash:
#                 logger.info(f'Not found passphrase')
#                 raise HTTPException(status_code=404, detail="Нет пароля или записи в базе данных")
#             #Проверка верности пароля 
#             if not ldap_pbkdf2_sha256.verify(delete.passphrase, password_hash['passphrase']):
#                 logger.info('password is not verify')
#                 raise HTTPException(status_code=403, detail='Неверный пароль')
#             #Удаление поля из таблицы по значению секретного ключа(id)
#             cursor.execute(
#                 '''
#                 DELETE FROM secrets_users 
#                 WHERE id = %s
#                 ''',
#                 (secret_key,))
#             #Логирование секретного ключа, айпи, и времени удаления секрета(delete_secret)
#             cursor.execute(
#                 '''
#                 INSERT INTO logger_secrets 
#                 (secret_key, ip_client, delete_secret) 
#                 VALUES 
#                 (%s, %s, %s);
#                 ''',
#                 (delete.secret_key, ip_client, datetime.now()))
#             conn.commit()
#             logger.info(f'Delete secret from db')
#             response = JSONResponse(content={'status': 'secret_deleted'})
#             return add_no_cache_headers(response)
#     except ResponseValidationError as e:
#         logger.info(f'No hash {password_hash['passphrase']} and {passphrase}')
#         raise HTTPException(status_code=404, detail='Неверный пароль')
#     except Exception as e:
#         logger.info(f'WARNING HASH')
#         raise HTTPException(status_code=400, detail='Неизвестная ошибка')
#     except psycopg2.Error as e:
#                 conn.rollback()
#                 raise HTTPException(status_code=400, detail="Ошибка базы данных")
    
