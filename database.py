from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException

connection_db = {
    'dbname': 'mydatabase',
    'user': 'postgres',
    'password': '2710',
    'host': 'localhost',
    'port': '5432'
}

@contextmanager
def start_table():
    conn = None
    try:
        conn = psycopg2.connect(**connection_db, cursor_factory=RealDictCursor)
        yield conn 
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f'Databasae error: {e}')
    finally:
        if conn:
            conn.close()

def get_db():
    """Функция-зависимость для FastAPI"""
    with start_table() as conn:
        yield conn