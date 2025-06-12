from fastapi import HTTPException
from passlib.hash import ldap_pbkdf2_sha256 

from app.services.encrypt import EncryptManager

encrypt = EncryptManager()

class DeleteSecretDB():
    def __init__(self, connection_db):
        self.cursor = connection_db

    def del_secret(self, key, passphrase):
        try:
            self.cursor.execute(
                """
                SELECT passphrase
                FROM secrets_users 
                WHERE id = %s and last_add > NOW()
                """, 
                (key.secret_key,))
            secret_dict = self.cursor.fetchall()

            if not secret_dict:
                raise HTTPException(404, 'секрет не нашли')
            if not ldap_pbkdf2_sha256.verify(passphrase, secret_dict['passphrase']):
                raise HTTPException(status_code=403, detail='Неверный пароль')
            
            self.cursor.execute(
                '''
                DELETE FROM secrets_users 
                WHERE id = %s
                ''',
                (key,))
            
            return True
        except:
            raise HTTPException(400, 'warning')

class DeleteSecretCACHE():
    def __init__(self, conntection_redis):
        self.r = conntection_redis

    def del_secret(self, key, passphrase):
        secret_off_redis = self.r.exists(key)
        if not secret_off_redis:
            HTTPException('404', 'secret not found')
        if not ldap_pbkdf2_sha256.verify(passphrase, secret_off_redis['passphrase']):
                raise HTTPException(status_code=403, detail='Неверный пароль')
        self.r.hdel(key)
        return True