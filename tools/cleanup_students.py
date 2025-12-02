import mysql.connector

WHITELIST = [
    '2023026054', # 정재영
    '2023026002', # 박가령
    '2023026045', # 이예인
    '2023026013', # 김규리
    '2025029013', # 이서아
    '2024026049', # 연수진
    '2021026017', # 정승원
]

DB = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def main():
    conn = mysql.connector.connect(**DB)
    cur = conn.cursor()

    # 확인: 현재 학생 목록
    cur.execute("SELECT student_id FROM students")
    all_students = [row[0] for row in cur.fetchall()]
    to_delete = [sid for sid in all_students if sid not in WHITELIST]

    print(f"전체 학생 {len(all_students)}명, 삭제 대상 {len(to_delete)}명: {to_delete}")
    if not to_delete:
        print("삭제할 학생이 없습니다.")
        cur.close(); conn.close(); return

    # 외래키 순서대로 삭제
    # 1) notification_recipients (받는 사람)
    cur.execute(
        f"DELETE FROM notification_recipients WHERE recipient_id IN ({','.join(['%s']*len(to_delete))})",
        to_delete
    )
    print(f"notification_recipients 삭제: {cur.rowcount}")

    # 2) graduation_analysis
    cur.execute(
        f"DELETE FROM graduation_analysis WHERE student_id IN ({','.join(['%s']*len(to_delete))})",
        to_delete
    )
    print(f"graduation_analysis 삭제: {cur.rowcount}")

    # 3) course_records
    cur.execute(
        f"DELETE FROM course_records WHERE student_id IN ({','.join(['%s']*len(to_delete))})",
        to_delete
    )
    print(f"course_records 삭제: {cur.rowcount}")

    # 4) students
    cur.execute(
        f"DELETE FROM students WHERE student_id IN ({','.join(['%s']*len(to_delete))})",
        to_delete
    )
    print(f"students 삭제: {cur.rowcount}")

    # 5) users (해당 학번 계정)
    cur.execute(
        f"DELETE FROM users WHERE username IN ({','.join(['%s']*len(to_delete))})",
        to_delete
    )
    print(f"users 삭제: {cur.rowcount}")

    conn.commit()
    cur.close(); conn.close()
    print("정리 완료")

if __name__ == '__main__':
    main()
