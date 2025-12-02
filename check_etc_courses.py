import mysql.connector

conn = mysql.connector.connect(
    host='203.255.78.58',
    port=9003,
    database='graduation_system',
    user='user29',
    password='123'
)

cur = conn.cursor(dictionary=True)
cur.execute("""
    SELECT course_name, category, area, credit 
    FROM course_records 
    WHERE student_id='2023026002' AND category NOT IN ('교양', '전공')
""")

rows = cur.fetchall()
print("박가령 학생 일선/기타 과목:")
print("="*80)
for r in rows:
    print(f"{r['course_name']:40s} | cat={r['category']:10s} | area={r['area'] or 'None':15s} | {r['credit']}학점")

cur.close()
conn.close()
