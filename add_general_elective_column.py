import mysql.connector

try:
    conn = mysql.connector.connect(
        host='203.255.78.58',
        port=9003,
        user='user29',
        password='123',
        database='graduation_system'
    )
    
    cursor = conn.cursor()
    
    # general_elective_credits 컬럼 추가
    try:
        cursor.execute('''
            ALTER TABLE students 
            ADD COLUMN general_elective_credits FLOAT DEFAULT NULL
        ''')
        conn.commit()
        print("general_elective_credits 컬럼 추가 완료")
    except mysql.connector.Error as e:
        if 'Duplicate column name' in str(e):
            print("general_elective_credits 컬럼이 이미 존재합니다.")
        else:
            raise
    
    cursor.close()
    conn.close()
    print("완료")
    
except Exception as e:
    print(f"오류 발생: {e}")
