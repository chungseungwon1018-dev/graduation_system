import mysql.connector, json

db = dict(host='203.255.78.58', port=9003, user='user29', password='123', database='graduation_system')

conn = mysql.connector.connect(**db)
cur = conn.cursor(dictionary=True)

print('=== 최근 분석 5건 ===')
cur.execute("SELECT ga.student_id, ga.analysis_date, ga.overall_completion_rate, ga.total_completed_credits, ga.total_required_credits, ga.analysis_result FROM graduation_analysis ga ORDER BY ga.analysis_date DESC LIMIT 5")
rows = cur.fetchall()
for i, r in enumerate(rows, 1):
    print(f"\n[{i}] 학생:{r['student_id']} 일시:{r['analysis_date']} 이수율:{r['overall_completion_rate']}% 이수:{r['total_completed_credits']}/{r['total_required_credits']}")
    try:
        data = json.loads(r['analysis_result']) if r['analysis_result'] else {}
    except Exception as e:
        print(f"  analysis_result JSON 파싱 실패: {e}")
        data = {}
    reqs = data.get('requirements_analysis', [])
    cats = {}
    for req in reqs:
        cats.setdefault(req.get('category'), 0)
        cats[req.get('category')] += 1
    print('  카테고리별 항목수:', cats)

    # 교양 항목 샘플 출력
    samples = [req for req in reqs if req.get('category')=='교양'][:5]
    for s in samples:
        print(f"    - 교양/{s.get('area')}: 완료 {s.get('completed_credits')}, 필요 {s.get('required_credits')}")

# 가장 최근 학생 상세 조회
if rows:
    sid = rows[0]['student_id']
    print(f"\n=== 최근 학생 상세: {sid} ===")
    cur.execute("SELECT student_id, name, department, admission_date, major_required_credits, major_elective_credits, general_elective_credits FROM students WHERE student_id=%s", (sid,))
    s = cur.fetchone()
    print(s)
    print('\n교과 카테고리 집계:')
    cur.execute("SELECT category, area, SUM(credit) as sum_credit FROM course_records WHERE student_id=%s AND grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P','통과') GROUP BY category, area ORDER BY category, area", (sid,))
    for row in cur.fetchall():
        print(f"  {row['category']}_{row['area']}: {row['sum_credit']}")

cur.close(); conn.close()
