from enhanced_xlsx_parser import EnhancedXlsxParser

DB_CONFIG = {'host':'203.255.78.58','port':9003,'database':'graduation_system','user':'user29','password':'123'}

files = ['샘플파일/test_sample_1.xlsx', '샘플파일/test_sample_3.xlsx']
parser = EnhancedXlsxParser(DB_CONFIG)

for f in files:
    print('\n--- Parsing', f, '---')
    try:
        personal_info, course_records = parser.parse_excel_file(f)
        print('학번:', personal_info.get('학번'))
        print('개인정보 항목수:', len(personal_info))
        print('과목수:', len(course_records))
        # print course_counts by category
        counts = {}
        for c in course_records:
            key = f"{c.get('구분')}_{c.get('영역')}" if c.get('영역') else c.get('구분')
            counts[key] = counts.get(key, 0) + (c.get('학점') or 0)
        print('이수학점 집계(항목별):', counts)
        print('Sample course rows:')
        for r in course_records[:10]:
            print('  ', r.get('구분'), r.get('영역'), r.get('교과목명'), r.get('학점'), r.get('성적'))
    except Exception as e:
        print('Error:', e)

parser.disconnect_db()
