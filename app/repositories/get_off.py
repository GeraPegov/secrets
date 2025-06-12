from fastapi import HTTPException
from passlib.hash import ldap_pbkdf2_sha256 

from app.services.encrypt import EncryptManager

encrypt = EncryptManager()

class ShowSecretDB():
    def __init__(self, connection_db):
        self.cursor = connection_db

    def get_secret(self, key, passphrase):
        try:
            self.cursor.execute(
                """
                SELECT secret, activity_status, passphrase
                FROM secrets_users 
                WHERE id = %s and last_add > NOW()
                """, 
                (key.secret_key,))
            secret_dict = self.cursor.fetchall()

            if not secret_dict:
                raise HTTPException(404, 'секрет не нашли')
            if secret_dict[0]['activity_status']:
                raise HTTPException(status_code=400, detail='Секрет уже просмотрели') 
            if not ldap_pbkdf2_sha256.verify(passphrase, secret_dict['passphrase']):
                raise HTTPException(status_code=403, detail='Неверный пароль')

            self.cursor.execute(
                """
                UPDATE secrets_users 
                SET show_secret = NOW(), activity_status = TRUE
                WHERE id = %s
                """,
                (key.secret_key,)
            )

            original_secret =  encrypt.encode_encrypt(secret_dict[0]['secret'])
            return original_secret
        except:
            raise HTTPException(400, 'warning')

class ShowSecretCACHE(ShowSecretDB):
    def __init__(self, conntection_redis):
        self.r = conntection_redis

    def get_secret(self, key, passphrase):
        secret_off_redis = self.r.exists(key)
        if not secret_off_redis:
            HTTPException('404', 'secret not found')
        if not ldap_pbkdf2_sha256.verify(passphrase, secret_off_redis['passphrase']):
                raise HTTPException(status_code=403, detail='Неверный пароль')
        original_secret =  encrypt.encode_encrypt(secret_off_redis)
        return original_secret