from enhanced_xlsx_parser import process_excel_file_enhanced
from graduation_requirements_checker import analyze_student_graduation

DB_CONFIG = {'host':'203.255.78.58','port':9003,'database':'graduation_system','user':'user29','password':'123'}

file_path = '샘플파일/test_sample_3.xlsx'
student_id = '2025029013'

# Process and save to DB
ok = process_excel_file_enhanced(file_path, student_id, DB_CONFIG)
print('process_excel_file_enhanced returned', ok)

# Run analysis
result = analyze_student_graduation(student_id, DB_CONFIG)
print('overall completion:', result.get('overall_completion_rate'))
print('total completed credits:', result.get('total_completed_credits'))
for r in result.get('requirements_analysis', []):
    print(r['category'], '/', r['area'], '-> completed', r['completed_credits'], 'required', r['required_credits'])
