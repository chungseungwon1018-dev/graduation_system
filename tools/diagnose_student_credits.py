import mysql.connector
from mysql.connector import Error

DB = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def main(student_id: str):
    try:
        conn = mysql.connector.connect(**DB)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM course_records WHERE student_id=%s ORDER BY year, semester, course_code", (student_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
    except Error as e:
        print('DB 오류:', e)
        return

    total = 0.0
    passed_total = 0.0
    target_codes = {'6208028','6208035'}
    target_info = []
    for r in rows:
        credit = float(r.get('credit') or 0)
        total += credit
        grade = (r.get('grade') or '').upper()
        completion = (r.get('completion_type') or '').upper()
        # passing heuristic same as checker
        passing = grade in {'A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P','PASS','통과','이수','합격'} or \
                  completion in {'A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P','PASS','통과','이수','합격'} or \
                  (credit>0 and any(kw in completion for kw in ['교양','전공','일선','일반선택','전공필수','전공선택','일반교양','확대교양'])) or \
                  (credit>0 and not grade and not completion)
        if passing:
            passed_total += credit
        code = (r.get('course_code') or '').strip()
        if code in target_codes:
            target_info.append({k:r.get(k) for k in ['year','semester','course_code','course_name','credit','grade','completion_type','category','area']})

    print(f"학생 {student_id} 수강기록 {len(rows)}건, 총 학점(raw)={total}, 통과 학점={passed_total}")
    print("특정 과목 확인:")
    for ti in target_info:
        print(ti)

if __name__=='__main__':
    import sys
    sid = sys.argv[1] if len(sys.argv)>1 else '2021026017'
    main(sid)
