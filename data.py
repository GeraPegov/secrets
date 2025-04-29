import psycopg2
from psycopg2.extras import RealDictCursor
import toml 
connect = psycopg2.connect(dbname='postgres', port='5432', host='localhost',user='postgres',password='2710', cursor_factory=RealDictCursor )
cursor = connect.cursor()
name = 'WERA'
cursor.execute('insert into secrets_users (secret) values (%s) returning id;', (name,))
data1 = cursor.fetchall()
cursor.execute('select * from secrets_users')
data = cursor.fetchall()
# connect.commit()
print(data)
print(data1[0]['id'])
