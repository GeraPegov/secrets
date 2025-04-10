from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException
import toml
with open("config.toml") as f:  
    data = toml.load(f)


@contextmanager
def start_table():
    conn = None
    try:
        conn = psycopg2.connect(dbname=data['dbname'], user=data['user'], password=data['password'], host=data['host'], port=data['port'], cursor_factory=RealDictCursor)
        yield conn 
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f'Databasae error: {e}')
    finally:
        if conn:
            conn.close()

def get_db():
    with start_table() as conn:
        yield conn