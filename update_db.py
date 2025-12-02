import mysql.connector
from mysql.connector import Error

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

try:
    # 데이터베이스 연결
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    
    # ALTER TABLE 명령 실행
    alter_table_query = """
    ALTER TABLE students
    ADD COLUMN phone VARCHAR(20) COMMENT '전화번호' AFTER admission_date,
    ADD COLUMN email VARCHAR(100) COMMENT '이메일' AFTER phone
    """
    
    cursor.execute(alter_table_query)
    connection.commit()
    print("테이블 수정 완료: phone, email 컬럼이 추가되었습니다.")
    
except Error as e:
    print(f"오류 발생: {e}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("데이터베이스 연결이 종료되었습니다.")