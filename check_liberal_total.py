import mysql.connector

conn = mysql.connector.connect(
    host='203.255.78.58',
    port=9003,
    database='graduation_system',
    user='user29',
    password='123'
)

cur = conn.cursor(dictionary=True)

# 박가령 전체 교양 과목
cur.execute("""
    SELECT course_name, credit, area 
    FROM course_records 
    WHERE student_id=%s AND category='교양'
    ORDER BY year, semester
""", ('2023026002',))

liberal_courses = cur.fetchall()

print("박가령 학생 교양 과목 전체:")
print("="*80)
area_sum = {}
for r in liberal_courses:
    area = r['area'] or '영역없음'
    credit = float(r['credit'])
    area_sum[area] = area_sum.get(area, 0) + credit
    print(f"{r['course_name']:45s} | {area:20s} | {credit}학점")

print("\n영역별 합계:")
print("="*80)
for area, total in sorted(area_sum.items()):
    print(f"{area:20s}: {total}학점")
print(f"{'총계':20s}: {sum(area_sum.values())}학점")

# 전공 과목
cur.execute("""
    SELECT SUM(credit) as total
    FROM course_records 
    WHERE student_id=%s AND category='전공'
""", ('2023026002',))
major_total = cur.fetchone()['total'] or 0

# 일선
cur.execute("""
    SELECT SUM(credit) as total
    FROM course_records 
    WHERE student_id=%s AND category NOT IN ('교양', '전공')
""", ('2023026002',))
etc_total = cur.fetchone()['total'] or 0

print(f"\n전공 과목 합계: {major_total}학점")
print(f"기타(일선 등): {etc_total}학점")
print(f"총 이수학점: {sum(area_sum.values()) + major_total + etc_total}학점")

cur.close()
conn.close()
