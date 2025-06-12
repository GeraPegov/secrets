from fastapi import FastAPI

from app.api.routers import api_router

app = FastAPI(
    title='Одноразовые секреты',
    description='Приложение для хранения секретов',
    version='1.0.0',
)

app.include_router(api_router)
