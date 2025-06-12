from fastapi import APIRouter, Depends, Query, HTTPException

from app.dependencies.delete import del_secret_db, del_secret_cache
from app.repositories.delete import DeleteSecretCACHE, DeleteSecretDB


router = APIRouter()

@router.get('/delete')
async def show_secret(
    secret_key: int = Query(...), 
    passphrase: str = Query(...),
    cache: DeleteSecretCACHE = Depends(del_secret_cache),
    database: DeleteSecretDB = Depends(del_secret_db),
    ) -> str:
    try:
        cache.del_secret(secret_key, passphrase)
        database.del_secret(secret_key, passphrase)
        return True
    except:
        raise HTTPException(404, 'warning')
