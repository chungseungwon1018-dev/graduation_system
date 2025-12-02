from enhanced_xlsx_parser import EnhancedXlsxParser, process_excel_file_enhanced

DB_CONFIG = {'host':'203.255.78.58','port':9003,'database':'graduation_system','user':'user29','password':'123'}

file_path = '샘플파일/test_sample_3.xlsx'
student_id = '2025123456'

# remove user if exists
import mysql.connector
conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute('DELETE FROM users WHERE username=%s', (student_id,))
conn.commit()
cur.close(); conn.close()

parser = EnhancedXlsxParser(DB_CONFIG)
try:
    personal_info, course_records = parser.parse_excel_file(file_path)
    print('parse ok', bool(personal_info))
finally:
    parser.disconnect_db()

# Now process file which should create user automatically
success, warnings = process_excel_file_enhanced(file_path, student_id, DB_CONFIG)
print('process success:', success, 'warnings:', warnings)

# Check users insertion
conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute('SELECT username FROM users WHERE username=%s', (student_id,))
print('user exists:', cur.fetchone())
cur.close(); conn.close()

print('process ok:', success)
