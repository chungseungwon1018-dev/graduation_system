import os
from enhanced_xlsx_parser import EnhancedXlsxParser

DB_CONFIG = {'host':'203.255.78.58','port':9003,'database':'graduation_system','user':'user29','password':'123'}

def test_parse_sample1():
    parser = EnhancedXlsxParser(DB_CONFIG)
    file_path = os.path.join('샘플파일','test_sample_1.xlsx')
    personal_info, course_records = parser.parse_excel_file(file_path)
    assert personal_info.get('학번') == '2021026017'
    assert len(course_records) >= 30
    assert float(personal_info.get('전공필수학점', 0)) == 24.0
    assert float(personal_info.get('전공선택학점', 0)) == 27.0
    assert float(personal_info.get('일반선택학점', 0)) == 1.0

def test_parse_sample3():
    parser = EnhancedXlsxParser(DB_CONFIG)
    file_path = os.path.join('샘플파일','test_sample_3.xlsx')
    personal_info, course_records = parser.parse_excel_file(file_path)
    assert personal_info.get('학번') == '2025029013'
    assert len(course_records) >= 6
    assert float(personal_info.get('전공필수학점', 0)) == 3.0
    assert float(personal_info.get('전공선택학점', 0)) == 6.0
    assert float(personal_info.get('일반선택학점', 0)) == 0.0
