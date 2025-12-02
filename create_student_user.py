import mysql.connector
import bcrypt

username = '2025029013'
password = 'testpass'
role = 'student'

hashpw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

conn = mysql.connector.connect(host='203.255.78.58',port=9003,user='user29',password='123',database='graduation_system')
cur = conn.cursor()
try:
    # check existing
    cur.execute('SELECT username FROM users WHERE username=%s', (username,))
    if cur.fetchone():
        print('user already exists')
    else:
        cur.execute('INSERT INTO users (username, password_hash, role, is_active, created_at) VALUES (%s, %s, %s, %s, NOW())', (username, hashpw, role, 1))
        conn.commit()
        print('user created')
finally:
    cur.close(); conn.close()
