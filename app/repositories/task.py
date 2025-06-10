from datetime import datetime

from fastapi import Depends

from database.database import get_db


class AddDatabase():

    def get_key(self, result_encrypt, result_hash, ip_client, conn=Depends(get_db)):
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO secrets_users 
            (secret, passphrase, ip_client) 
            VALUES 
            (%s, %s, %s) 
            RETURNING id;
            """,
            (result_hash, result_encrypt, ip_client))
        new_key = conn.cursor.fetchone()['id']
        conn.commit()
        return new_key


class AddLogger():
    def add_log(self, new_key, ip_client, conn = Depends(get_db)):
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO logger_secrets 
            (secret_key, ip_client, add_secret) 
            VALUES 
            (%s, %s, %s);
            ''',
            (new_key, ip_client, datetime.now()))
        conn.commit()
        return 