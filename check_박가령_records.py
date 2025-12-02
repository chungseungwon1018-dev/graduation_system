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
    SELECT course_name, credit, grade, completion_type, category, area 
    FROM course_records 
    WHERE student_id=%s 
    ORDER BY year, semester
    LIMIT 15
""", ('2023026002',))

rows = cur.fetchall()

print("박가령 학생 course_records 샘플:")
print("="*100)
for r in rows:
    print(f"{r['course_name']:40s} | credit={r['credit']} | grade={r['grade']} | completion={r['completion_type']} | cat={r['category']} | area={r['area']}")

cur.close()
conn.close()
