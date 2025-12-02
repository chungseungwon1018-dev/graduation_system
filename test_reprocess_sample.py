"""박가령 샘플 재처리 테스트 스크립트"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_xlsx_parser import process_excel_file_enhanced
from graduation_requirements_checker import analyze_student_graduation
import json

db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

# 테스트할 샘플 파일 목록
test_cases = [
    {'file': r'샘플파일\report_1759248078955_박가령.xlsx', 'student_id': '2023026002', 'name': '박가령'},
    {'file': r'샘플파일\report_1764415240667_정승원.xlsx', 'student_id': '2021026017', 'name': '정승원'},
    {'file': r'샘플파일\report_1761794821475_연수진.xlsx', 'student_id': '2023026003', 'name': '연수진'},
    {'file': r'샘플파일\report_1759295962875_이서아.xlsx', 'student_id': '2023026004', 'name': '이서아'},
    {'file': r'샘플파일\report_1759068230025_정재영.xlsx', 'student_id': '2023026054', 'name': '정재영'},
]

print("="*80)
print("샘플 파일 재처리 테스트")
print("="*80)

for case in test_cases:
    file_path = case['file']
    student_id = case['student_id']
    name = case['name']
    
    print(f"\n{'='*80}")
    print(f"처리 중: {name} ({student_id})")
    print(f"파일: {file_path}")
    print("="*80)
    
    if not os.path.exists(file_path):
        print(f"⚠️ 파일을 찾을 수 없습니다: {file_path}")
        continue
    
    try:
        # 파싱 및 DB 저장
        print("\n[1단계] Excel 파싱 및 DB 저장...")
        success, warnings = process_excel_file_enhanced(file_path, student_id, db_config)
        
        if not success:
            print(f"❌ 파싱 실패")
            continue
        
        print(f"✅ 파싱 성공")
        if warnings:
            print(f"⚠️ 경고 메시지:")
            for w in warnings:
                print(f"   - {w}")
        
        # 졸업 요건 분석
        print("\n[2단계] 졸업 요건 분석...")
        analysis = analyze_student_graduation(student_id, db_config, warnings)
        
        if 'error' in analysis:
            print(f"❌ 분석 실패: {analysis['error']}")
            continue
        
        print(f"✅ 분석 완료")
        
        # 주요 결과 출력
        print(f"\n{'='*80}")
        print(f"📊 분석 결과: {name} ({student_id})")
        print(f"{'='*80}")
        print(f"총 이수학점: {analysis['total_completed_credits']}학점")
        print(f"졸업 필요학점: {analysis['total_required_credits']}학점")
        print(f"전체 이수율: {analysis['overall_completion_rate']}%")
        
        print(f"\n[전공]")
        major_detail = analysis.get('major_detail', {})
        print(f"  전공필수: {major_detail.get('전공필수', 0)}학점")
        print(f"  전공선택: {major_detail.get('전공선택', 0)}학점")
        
        print(f"\n[교양]")
        liberal_detail = analysis.get('liberal_arts_detail', {})
        for area, credits in liberal_detail.items():
            print(f"  {area}: {credits}학점")
        print(f"  교양 상한: {analysis.get('liberal_arts_cap', 0)}학점")
        print(f"  교양 초과분: {analysis.get('liberal_arts_overflow', 0)}학점")
        
        print(f"\n[일반선택]")
        general_detail = analysis.get('general_elective_detail', {})
        print(f"  일반선택: {general_detail.get('일반선택', 0)}학점")
        
        if analysis.get('missing_requirements'):
            print(f"\n[미달 요건] ({len(analysis['missing_requirements'])}개)")
            for req in analysis['missing_requirements'][:3]:
                print(f"  - {req['category']} {req['area']}: {req['missing_credits']}학점 부족")
            if len(analysis['missing_requirements']) > 3:
                print(f"  ... 외 {len(analysis['missing_requirements']) - 3}개")
        else:
            print(f"\n✅ 모든 요건 충족!")
        
        # 파싱 경고
        if analysis.get('parsing_warnings'):
            print(f"\n[파싱 경고]")
            for w in analysis['parsing_warnings']:
                print(f"  - {w}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*80}")
print("테스트 완료")
print("="*80)
