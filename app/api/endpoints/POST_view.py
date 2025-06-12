from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.showsecret import get_secret_cache, get_secret_db
from app.repositories.get_off import ShowSecretCACHE, ShowSecretDB

router = APIRouter()


@router.get('/secret/viewing')
async def view_secret(
        secret_key: int = Query(...),
        passphrase: str = Query(...),
        cache: ShowSecretCACHE = Depends(get_secret_cache),
        database: ShowSecretDB = Depends(get_secret_db),
        ) -> str:
    try:
        сheck_cache = cache.get_secret(secret_key, passphrase)
        if сheck_cache:
            return сheck_cache
        check_db = database.get_secret(secret_key, passphrase)
        return check_db
    except Exception as e:
        raise HTTPException(404, f'Непредвиденная ошибка: {str(e)}')
