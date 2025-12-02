import sys
import os
import mysql.connector
from mysql.connector import Error

# Ensure project root on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from graduation_requirements_checker import analyze_student_graduation

DB_CONFIG = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def pick_student_id(conn):
    cur = conn.cursor()
    # course_records가 있는 학생 우선 선택
    cur.execute("SELECT student_id, COUNT(*) AS cnt FROM course_records GROUP BY student_id ORDER BY cnt DESC LIMIT 1")
    row = cur.fetchone()
    if row and row[0]:
        sid = row[0]
        cur.close()
        return sid
    # fallback: 아무 학생이나
    cur.execute("SELECT student_id FROM students ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None


def main():
    student_id = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print("DB 연결 실패:", e)
        sys.exit(1)

    try:
        if not student_id:
            student_id = pick_student_id(conn)
        if not student_id:
            print("학생 ID를 찾지 못했습니다. 인자로 학번을 넘겨주세요.")
            sys.exit(2)

        print(f"분석 대상 학번: {student_id}")
        # 부가 디버그: 학생 정보에서 학과/입학연도 추출
        cur = conn.cursor()
        cur.execute("SELECT department, admission_date FROM students WHERE student_id=%s", (student_id,))
        row = cur.fetchone()
        dept = row[0] if row else None
        year = None
        if row and row[1]:
            try:
                year = int(str(row[1])[:4])
            except Exception:
                pass
        print(f"학생 학과/입학연도: {dept} / {year}")

        # 교양 상한 디버그: graduation_requirements에서 교양 max_credits 확인
        if dept and year:
            cur.execute("SELECT area, required_credits, max_credits FROM graduation_requirements WHERE department=%s AND admission_year=%s AND category='교양'", (dept, year))
            rows = cur.fetchall()
            caps = [float(r[2]) for r in rows if r[2] is not None]
            cap_val = max(caps) if caps else None
            print(f"요건표 기준 교양 상한(max_credits): {cap_val}")

        # 교양 원시합 디버그: course_records에서 교양 합산
        cur.execute("SELECT area, SUM(credit) FROM course_records WHERE student_id=%s AND category='교양' GROUP BY area", (student_id,))
        area_rows = cur.fetchall()
        raw_sum = 0.0
        if area_rows:
            print("교양 세부영역별 원시 합계:")
            for ar, sm in area_rows:
                raw_sum += float(sm or 0)
                print(f"- {ar or '-'}: {sm}")
        print(f"교양 원시 총합: {raw_sum}")

        result = analyze_student_graduation(student_id, DB_CONFIG)
        if 'error' in result:
            print("분석 실패:", result['error'])
            sys.exit(3)

        print("=== 분석 요약 ===")
        print("이수학점(상단 표시):", result.get('total_completed_credits'))
        print("필요학점 합계:", result.get('total_required_credits'))
        print("전체 이수율:", result.get('overall_completion_rate'), "%")

        # 교양 관련 행만 요약 출력
        liberal_rows = [r for r in result.get('requirements_analysis', []) if r.get('category') == '교양']
        if liberal_rows:
            print("\n[교양 영역 요약]")
            for r in liberal_rows:
                area = r.get('area') or '-'
                print(f"- {area}: 이수 {r.get('completed_credits')} / 필요 {r.get('required_credits')}")
        else:
            print("\n[교양 영역 요약] 표시할 교양 요건 행이 없습니다 (상한 적용은 상단 총계에 반영됨)")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
