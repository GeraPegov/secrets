import toml
import psycopg2
from database import start_table
from datetime import datetime, timedelta
examples_secret = 'my secret'
examples_passphrase = 'my passphrase'
examples_first_add = datetime(2025, 4, 22, 9, 37, 54, 166071)
examples_ip_client = '127.2.3.54'
examples_show_secret = datetime(2025, 4, 22, 9, 37, 54, 166071)

def test_cleardb():
    with start_table() as conn:
        with conn.cursor() as curs:
            curs.execute(
            '''
            INSERT INTO test_programm
            (secret, passphrase, first_add, ip_client, show_secret)
            VALUES
            (%s, %s, %s, %s, %s)
            RETURNING 
            id;
            ''', 
            (examples_secret, examples_passphrase, examples_first_add, examples_ip_client, examples_show_secret)
            )
            insert_id = curs.fetchone()['id']
            # id, secret, passphrase, first_add, last_add, activity_status, ip_client, show_secret
            curs.execute(
            '''
            DELETE
            FROM test_programm 
            WHERE first_add < NOW() 
            RETURNING
            id, secret, passphrase, first_add, last_add, activite_show, ip_client, show_secret;
            ''')
            delete = curs.fetchall()[0]
            delete_id = delete['id']
            delete_secret = delete['secret']
            delete_passphrase = delete['passphrase']
            delete_first_add = delete['first_add']
            delete_last_add = delete['last_add']
            delete_activity_status = delete['activite_show']
            delete_ip_client = delete['ip_client']
            delete_show_secret = delete['show_secret']
            assert insert_id == delete_id
            assert delete_secret == examples_secret
            assert delete_passphrase == examples_passphrase
            assert delete_first_add == examples_first_add
            assert delete_last_add == examples_first_add + timedelta(minutes=60)
            assert delete_activity_status == False
            assert delete_ip_client == examples_ip_client
            assert delete_show_secret == examples_show_secret



