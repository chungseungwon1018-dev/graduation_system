from enhanced_xlsx_parser import EnhancedXlsxParser

file_path = '샘플파일/test_sample_3.xlsx'
parser = EnhancedXlsxParser({'host':'203.255.78.58','port':9003,'database':'graduation_system','user':'user29','password':'123'})
try:
    personal_info, course_records = parser.parse_excel_file(file_path)
    print('PERSONAL INFO:')
    for k,v in personal_info.items():
        print('  ', k, ':', v)
    print('\nCOURSE RECORDS COUNT:', len(course_records))
    for i, rec in enumerate(course_records[:20]):
        print(f"  [{i+1}] {rec.get('구분') or ''} | {rec.get('영역') or ''} | {rec.get('세부영역') or ''} | {rec.get('교과목명') or ''} | {rec.get('학점') or ''} | {rec.get('성적') or ''}")
except Exception as e:
    print('Error:', e)
finally:
    parser.disconnect_db()
