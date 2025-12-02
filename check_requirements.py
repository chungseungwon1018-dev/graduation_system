import mysql.connector

conn = mysql.connector.connect(
    host='203.255.78.58',
    port=9003,
    user='user29',
    password='123',
    database='graduation_system'
)

cursor = conn.cursor()

# 먼저 어떤 입학연도가 있는지 확인
cursor.execute('SELECT DISTINCT admission_year FROM graduation_requirements WHERE department="경영정보학과" ORDER BY admission_year')
years = cursor.fetchall()
print("=== 입학연도 목록 ===")
for y in years:
    print(f"입학연도: {y[0]}")

print("\n=== 입학연도별 졸업요건 ===")
for year in years:
    print(f"\n[{year[0]}학번]")
    cursor.execute('SELECT category, area, required_credits FROM graduation_requirements WHERE department="경영정보학과" AND admission_year=%s ORDER BY category, area', (year[0],))
    rows = cursor.fetchall()
    for r in rows:
        print(f"  {r[0]} - {r[1]}: {r[2]}학점")

cursor.close()
conn.close()
