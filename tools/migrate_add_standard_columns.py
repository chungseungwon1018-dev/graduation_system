import mysql.connector
from mysql.connector import Error

db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute("SHOW COLUMNS FROM {} LIKE %s".format(table), (column,))
    return cursor.fetchone() is not None

def ensure_students_columns(cursor):
    to_add = []
    if not column_exists(cursor, 'students', 'phone'):
        to_add.append("ADD COLUMN phone VARCHAR(20) COMMENT '전화번호' AFTER admission_date")
    if not column_exists(cursor, 'students', 'email'):
        to_add.append("ADD COLUMN email VARCHAR(100) COMMENT '이메일' AFTER phone")
    if not column_exists(cursor, 'students', 'major_required_credits'):
        to_add.append("ADD COLUMN major_required_credits FLOAT DEFAULT NULL COMMENT '전공필수학점' AFTER counseling_count")
    if not column_exists(cursor, 'students', 'major_elective_credits'):
        to_add.append("ADD COLUMN major_elective_credits FLOAT DEFAULT NULL COMMENT '전공선택학점' AFTER major_required_credits")
    if not column_exists(cursor, 'students', 'general_elective_credits'):
        to_add.append("ADD COLUMN general_elective_credits FLOAT DEFAULT NULL COMMENT '일반선택학점' AFTER major_elective_credits")
    if to_add:
        alter = f"ALTER TABLE students {', '.join(to_add)}"
        print('Executing:', alter)
        cursor.execute(alter)
        print('students table updated')
    else:
        print('students table already contains the standard columns')

def ensure_graduation_requirements_columns(cursor):
    if not column_exists(cursor, 'graduation_requirements', 'max_credits'):
        alter = "ALTER TABLE graduation_requirements ADD COLUMN max_credits DECIMAL(4,1) NULL AFTER required_credits"
        print('Executing:', alter)
        cursor.execute(alter)
        print('graduation_requirements updated')
    else:
        print('graduation_requirements already has max_credits')

def main():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        ensure_students_columns(cursor)
        ensure_graduation_requirements_columns(cursor)
        conn.commit()
    except Error as e:
        print('Migration error:', e)
        conn.rollback()
    finally:
        cursor.close(); conn.close()
        print('Done')

if __name__ == '__main__':
    main()
