import mysql.connector
from mysql.connector import Error
from graduation_requirements_checker import analyze_student_graduation

DB = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def main():
    try:
        conn = mysql.connector.connect(**DB)
        cur = conn.cursor()
        cur.execute("SELECT student_id FROM students ORDER BY student_id")
        ids = [row[0] for row in cur.fetchall()]
        cur.close(); conn.close()
    except Error as e:
        print('DB 오류:', e)
        return

    print('재분석 대상 학생 수:', len(ids))
    for sid in ids:
        res = analyze_student_graduation(sid, DB)
        ok = 'error' not in res
        print(f"{sid}: {'OK' if ok else 'ERR'} - total={res.get('total_completed_credits')} rate={res.get('overall_completion_rate')}" )

if __name__ == '__main__':
    main()
