from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import contextmanager
import logging 
from log import start_logging
import psycopg2
from schemas import User_add
from database import get_db


app = FastAPI()

templates = Jinja2Templates(directory="templates")


start_logging()
logger =logging.getLogger(__name__)





@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):

    return templates.TemplateResponse("form.html", {"request": request})


@app.post('/secret')
async def add_secret(secret: str = Form(...), passphrase:str = Form(...), conn = Depends(get_db)):
    try:
        
        ttl_seconds = 3600
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO secrets_users (secret, passphrase, ttl_seconds) VALUES (%s, %s, %s) RETURNING *;",
                (secret, passphrase, ttl_seconds)
            )
            new_item = cursor.fetchall()
            conn.commit()
            return new_item
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    
@app.get('/secret/{password}')
async def show_secret(password: str, conn = Depends(get_db)):
    try:
        
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT secret FROM secrets_users WHERE passphrase = {password}"
            )
            new_item = cursor.fetchall()
            conn.commit()
            return new_item
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=400)
    
# @app.get('/secrets')
# async def show_secret()

#5432