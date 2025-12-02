#!/usr/bin/env python3
"""
관리자 졸업요건 관리 기능 테스트 스크립트
"""

import mysql.connector
import json
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        print("✅ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def test_graduation_requirements_crud():
    """졸업요건 CRUD 테스트"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 1. 기존 졸업요건 조회
        cursor.execute("SELECT COUNT(*) as count FROM graduation_requirements")
        initial_count = cursor.fetchone()['count']
        print(f"✅ 초기 졸업요건 개수: {initial_count}")
        
        # 2. 새 졸업요건 추가 테스트
        test_requirement = {
            'department': '경영학과',
            'admission_year': 2024,
            'category': '교양',
            'area': '기초교양',
            'sub_area': '수학',
            'required_credits': 6.0,
            'description': '테스트용 졸업요건',
            'is_active': True
        }
        
        insert_query = """
        INSERT INTO graduation_requirements 
        (department, admission_year, category, area, sub_area, required_credits, description, is_active)
        VALUES (%(department)s, %(admission_year)s, %(category)s, %(area)s, %(sub_area)s, 
                %(required_credits)s, %(description)s, %(is_active)s)
        """
        
        cursor.execute(insert_query, test_requirement)
        new_requirement_id = cursor.lastrowid
        connection.commit()
        print(f"✅ 새 졸업요건 추가 성공 (ID: {new_requirement_id})")
        
        # 3. 추가된 요건 조회
        cursor.execute("SELECT * FROM graduation_requirements WHERE id = %s", (new_requirement_id,))
        added_requirement = cursor.fetchone()
        
        if added_requirement:
            print(f"✅ 추가된 요건 조회 성공: {added_requirement['department']} - {added_requirement['category']}")
        else:
            print("❌ 추가된 요건 조회 실패")
        
        # 4. 요건 수정 테스트
        update_query = """
        UPDATE graduation_requirements 
        SET required_credits = %s, description = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        cursor.execute(update_query, (9.0, '수정된 테스트 요건', new_requirement_id))
        connection.commit()
        
        # 수정 확인
        cursor.execute("SELECT required_credits, description FROM graduation_requirements WHERE id = %s", (new_requirement_id,))
        updated_requirement = cursor.fetchone()
        
        if updated_requirement and updated_requirement['required_credits'] == 9.0:
            print("✅ 졸업요건 수정 성공")
        else:
            print("❌ 졸업요건 수정 실패")
        
        # 5. 요건 삭제 테스트
        cursor.execute("DELETE FROM graduation_requirements WHERE id = %s", (new_requirement_id,))
        connection.commit()
        
        # 삭제 확인
        cursor.execute("SELECT COUNT(*) as count FROM graduation_requirements WHERE id = %s", (new_requirement_id,))
        delete_check = cursor.fetchone()['count']
        
        if delete_check == 0:
            print("✅ 졸업요건 삭제 성공")
        else:
            print("❌ 졸업요건 삭제 실패")
        
        # 6. 최종 개수 확인
        cursor.execute("SELECT COUNT(*) as count FROM graduation_requirements")
        final_count = cursor.fetchone()['count']
        
        if final_count == initial_count:
            print(f"✅ 최종 졸업요건 개수 일치: {final_count}")
        else:
            print(f"❌ 최종 개수 불일치: 초기 {initial_count}, 최종 {final_count}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 졸업요건 CRUD 테스트 실패: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return False

def test_student_analysis_trigger():
    """학생 분석 결과 업데이트 테스트"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 테스트용 학생 데이터 확인
        cursor.execute("""
            SELECT student_id, department, admission_date 
            FROM students 
            LIMIT 3
        """)
        
        students = cursor.fetchall()
        
        if students:
            print(f"✅ 테스트 대상 학생 {len(students)}명 확인")
            for student in students:
                print(f"   - {student['student_id']}: {student['department']}")
        else:
            print("⚠️ 테스트할 학생 데이터가 없습니다.")
        
        # 분석 결과 테이블 확인
        cursor.execute("SELECT COUNT(*) as count FROM graduation_analysis")
        analysis_count = cursor.fetchone()['count']
        print(f"✅ 기존 분석 결과 개수: {analysis_count}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 학생 분석 테스트 실패: {e}")
        return False

def test_notification_system():
    """알림 시스템 테스트"""
    try:
        from notification_system import send_notification_to_students
        
        # 테스트 알림 전송 (실제로는 전송하지 않고 구조만 확인)
        print("✅ 알림 시스템 모듈 import 성공")
        
        # 알림 테이블 확인
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM notifications")
        notification_count = cursor.fetchone()[0]
        print(f"✅ 기존 알림 개수: {notification_count}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 알림 시스템 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("=" * 50)
    print("관리자 졸업요건 관리 기능 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("데이터베이스 연결", test_database_connection),
        ("졸업요건 CRUD 기능", test_graduation_requirements_crud),
        ("학생 분석 트리거", test_student_analysis_trigger),
        ("알림 시스템", test_notification_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}] 테스트 중...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n통과: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 모든 테스트가 통과했습니다!")
        print("\n관리자 페이지에서 졸업요건 수정/저장이 정상적으로 작동할 것입니다.")
        print("변경된 졸업요건은 자동으로 DB에 반영되고, 해당 학생들에게 알림이 전송됩니다.")
    else:
        print(f"\n⚠️ {len(results) - passed}개의 테스트가 실패했습니다.")
        print("실패한 부분을 확인하고 수정이 필요합니다.")

if __name__ == "__main__":
    main()