from fastapi import APIRouter

from app.api.endpoints.GET_home import router as router_home
from app.api.endpoints.GET_secret import router as router_add_secret
from app.api.endpoints.POST_delete import router as router_delete_secret
from app.api.endpoints.POST_view import router as router_viewing_secret

api_router = APIRouter()

api_router.include_router(
    router_home,
    tags=['Home']
)

api_router.include_router(
    router_add_secret,
    tags=['Add']
)

api_router.include_router(
    router_delete_secret,
    tags=['Delete']
)

api_router.include_router(
    router_viewing_secret,
    tags=['View']
)
