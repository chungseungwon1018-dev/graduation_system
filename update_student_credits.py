import mysql.connector

conn = mysql.connector.connect(
    host='203.255.78.58',
    port=9003,
    user='user29',
    password='123',
    database='graduation_system'
)

cursor = conn.cursor()

# 학생 2021026017의 전공필수/전공선택/일반선택 학점 업데이트
# test_sample_1.xlsx 기준: AC22=24, AH22=27, Y22=1
student_id = '2021026017'
major_required = 24.0
major_elective = 27.0
general_elective = 1.0

cursor.execute('''
    UPDATE students 
    SET major_required_credits = %s, major_elective_credits = %s, general_elective_credits = %s, updated_at = NOW()
    WHERE student_id = %s
''', (major_required, major_elective, general_elective, student_id))

conn.commit()

print(f"학번 {student_id}의 전공필수/전공선택/일반선택 학점 업데이트 완료")
print(f"  전공필수: {major_required}학점")
print(f"  전공선택: {major_elective}학점")
print(f"  일반선택: {general_elective}학점")

# 확인
cursor.execute('SELECT major_required_credits, major_elective_credits, general_elective_credits FROM students WHERE student_id=%s', (student_id,))
result = cursor.fetchone()
print(f"\n확인: {result}")

cursor.close()
conn.close()
