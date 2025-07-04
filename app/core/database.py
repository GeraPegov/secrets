from contextlib import contextmanager

import psycopg2
from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from app.core.config import settings


@contextmanager
def start_table():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            client_encoding='utf8',
            cursor_factory=RealDictCursor
        )
        yield conn 
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f'Databasae error: {e}')
    finally:
        if conn:
            conn.close()


def get_db():
    with start_table() as conn:
        yield conn


def init_db():
    with start_table() as conn:
        with conn.cursor() as curs:
            """
            id = выдается как "секретный ключ"
            secret = секрет пользователя(шифруется)
            passphrase = пароль пользователя(кешируется)
            first_add = время первого добавления секрета
            last_add = вычисляется. через 60 минут секрет становится не доступен
            activity_status = Изначально False, менятся на True(просмотрено)
            ip_client = айпи клиента 
            show_secret = время просмотра секрета
            """
            curs.execute(
                '''
                CREATE TABLE IF NOT EXISTS secrets_users(
                id SERIAL PRIMARY KEY,
                secret TEXT,
                passphrase TEXT,
                first_add TIMESTAMP DEFAULT NOW(),
                last_add TIMESTAMP GENERATED ALWAYS AS(first_add + INTERVAL '60 minutes') STORED,
                activity_status BOOLEAN DEFAULT FALSE,
                ip_client TEXT,
                show_secret TIMESTAMP
                );
                '''
            )
            """
            ip_user = айпи клиента
            secret_key = секретный ключ(id из таблицы secret_user)
            delete_secret = время удаления секрета
            add_secret = время добавления секрета
            time_reading = время просмотра секрета
            """
            curs.execute(
                '''
                CREATE TABLE IF NOT EXISTS logger_secrets(
                id SERIAL PRIMARY KEY,
                ip_client TEXT,
                secret_key INTEGER,
                delete_secret TEXT,
                add_secret TEXT,
                time_reading TEXT
                );
                '''
            )
            curs.execute(
                '''
                CREATE TABLE IF NOT EXISTS test_programm(
                id SERIAL PRIMARY KEY,
                secret TEXT,
                passphrase TEXT,
                first_add TIMESTAMP DEFAULT NOW(),
                last_add TIMESTAMP GENERATED ALWAYS AS(first_add + INTERVAL '60 minutes') STORED,
                activite_show BOOLEAN DEFAULT FALSE,
                ip_client TEXT,
                show_secret TIMESTAMP,
                secret_key INTEGER,
                delete_secret TEXT,
                add_secret TEXT,
                time_reading TEXT
                );
                '''
            )
            conn.commit()