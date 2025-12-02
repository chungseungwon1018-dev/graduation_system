import mysql.connector

conn = mysql.connector.connect(
    host='203.255.78.58',
    port=9003,
    user='user29',
    password='123',
    database='graduation_system'
)

cursor = conn.cursor(dictionary=True)

# test_sample_1.xlsx로 업로드된 학생 정보 확인 (최근 업로드)
cursor.execute('SELECT student_id, name, department, admission_date, major_required_credits, major_elective_credits FROM students ORDER BY student_id DESC LIMIT 5')
students = cursor.fetchall()

print("=== 최근 등록된 학생 5명 ===")
for s in students:
    print(f"학번: {s['student_id']}, 이름: {s['name']}, 입학일: {s['admission_date']}")
    print(f"  전공필수: {s['major_required_credits']}, 전공선택: {s['major_elective_credits']}")

# 첫 번째 학생의 수강 과목 확인
if students:
    student_id = students[0]['student_id']
    print(f"\n=== {student_id} 학생의 수강 과목 ===")
    cursor.execute('SELECT category, area, sub_area, course_name, credit, grade FROM course_records WHERE student_id=%s', (student_id,))
    courses = cursor.fetchall()
    
    total_credits = {}
    for c in courses:
        cat = c['category']
        area = c['area'] if c['area'] else ''
        key = f"{cat}_{area}" if area else cat
        
        grade = str(c['grade']).upper()
        passing = grade in ['A+', 'A0', 'A-', 'B+', 'B0', 'B-', 'C+', 'C0', 'C-', 'D+', 'D0', 'P', '통과']
        
        if passing:
            total_credits[key] = total_credits.get(key, 0) + float(c['credit'])
        
        print(f"  [{c['category']}] {c['area'] or ''} - {c['course_name']}: {c['credit']}학점 ({c['grade']})")
    
    print(f"\n=== 이수학점 집계 ===")
    for key, credit in sorted(total_credits.items()):
        print(f"  {key}: {credit}학점")

cursor.close()
conn.close()
