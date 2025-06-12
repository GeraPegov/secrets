from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.delete import del_secret_cache, del_secret_db
from app.repositories.delete import DeleteSecretCACHE, DeleteSecretDB

router = APIRouter()


@router.get('/secret/delete')
async def delete_secret(
        secret_key: int = Query(...),
        passphrase: str = Query(...),
        cache: DeleteSecretCACHE = Depends(del_secret_cache),
        database: DeleteSecretDB = Depends(del_secret_db),
        ) -> dict:
    try:
        cache.del_secret(secret_key, passphrase)
        database.del_secret(secret_key, passphrase)
        response = {'status': 'success'}
        return response
    except Exception as e:
        raise HTTPException(404, f'Непредвиденная ошибка: {str(e)}')
