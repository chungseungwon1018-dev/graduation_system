import mysql.connector

conn = mysql.connector.connect(
    host='203.255.78.58',
    port=9003,
    database='graduation_system',
    user='user29',
    password='123'
)

cur = conn.cursor()

try:
    cur.execute('ALTER TABLE students ADD COLUMN major_required_credits FLOAT DEFAULT NULL')
    print('major_required_credits 컬럼 추가 완료')
except Exception as e:
    print(f'major_required_credits 추가 오류: {e}')

try:
    cur.execute('ALTER TABLE students ADD COLUMN major_elective_credits FLOAT DEFAULT NULL')
    print('major_elective_credits 컬럼 추가 완료')
except Exception as e:
    print(f'major_elective_credits 추가 오류: {e}')

conn.commit()
cur.close()
conn.close()
print('완료')
