from enhanced_xlsx_parser import process_excel_file_enhanced
from graduation_requirements_checker import analyze_student_graduation

DB_CONFIG = {'host':'203.255.78.58','port':9003,'database':'graduation_system','user':'user29','password':'123'}

file_path = '샘플파일/test_sample_3.xlsx'
student_id = '2025029013'

ok = process_excel_file_enhanced(file_path, student_id, DB_CONFIG)
print('process result:', ok)

success, warnings = ok if isinstance(ok, tuple) else (ok, [])
print('success:', success, 'warnings:', warnings)

analysis_result = analyze_student_graduation(student_id, DB_CONFIG, parsing_warnings=warnings)
print('analysis parsing_warnings:', analysis_result.get('parsing_warnings'))
print('overall:', analysis_result.get('overall_completion_rate'), 'completed:', analysis_result.get('total_completed_credits'))
