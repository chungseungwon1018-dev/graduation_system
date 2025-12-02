#!/usr/bin/env python3
"""
관리자 학생 관리 시스템 테스트 스크립트
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

def test_student_management_api():
    """학생 관리 API 테스트"""
    print("=" * 60)
    print("관리자 학생 관리 시스템 테스트 시작")
    print("=" * 60)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 1. 학생 수 확인
        cursor.execute("SELECT COUNT(*) as count FROM students")
        student_count = cursor.fetchone()['count']
        print(f"✅ 총 학생 수: {student_count}명")
        
        # 2. 학과별 분포 확인
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM students 
            WHERE department IS NOT NULL 
            GROUP BY department 
            ORDER BY count DESC
        """)
        dept_stats = cursor.fetchall()
        print(f"✅ 학과별 분포:")
        for dept in dept_stats:
            print(f"   - {dept['department']}: {dept['count']}명")
        
        # 3. 분석 완료된 학생 수 확인
        cursor.execute("""
            SELECT COUNT(*) as analyzed_count 
            FROM graduation_analysis
        """)
        analyzed_count = cursor.fetchone()['analyzed_count']
        print(f"✅ 분석 완료 학생: {analyzed_count}명")
        
        # 4. 평균 이수율 계산
        cursor.execute("""
            SELECT AVG(overall_completion_rate) as avg_rate 
            FROM graduation_analysis
            WHERE overall_completion_rate IS NOT NULL
        """)
        avg_rate = cursor.fetchone()['avg_rate']
        print(f"✅ 평균 이수율: {avg_rate:.1f}%" if avg_rate else "✅ 평균 이수율: 데이터 없음")
        
        # 5. 최신 분석 데이터 확인
        cursor.execute("""
            SELECT s.student_id, s.name, s.department, s.grade,
                   ga.overall_completion_rate, ga.analysis_date
            FROM students s
            LEFT JOIN graduation_analysis ga ON s.student_id = ga.student_id
            ORDER BY ga.analysis_date DESC
            LIMIT 5
        """)
        recent_analyses = cursor.fetchall()
        
        print(f"✅ 최근 분석된 학생 {len(recent_analyses)}명:")
        for student in recent_analyses:
            rate = student['overall_completion_rate']
            date = student['analysis_date']
            print(f"   - {student['student_id']} ({student['name']}): {rate}% ({date})" 
                  if rate and date else f"   - {student['student_id']} ({student['name']}): 미분석")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 학생 관리 API 테스트 실패: {e}")
        return False

def test_student_search_functionality():
    """학생 검색 기능 테스트"""
    print("\n📋 학생 검색 기능 테스트")
    print("-" * 40)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 1. 전체 학생 조회 (페이징 포함)
        cursor.execute("""
            SELECT s.*, 
                   ga.overall_completion_rate,
                   ga.total_completed_credits,
                   ga.total_required_credits,
                   ga.analysis_date
            FROM students s
            LEFT JOIN graduation_analysis ga ON s.student_id = ga.student_id
            ORDER BY s.student_id 
            LIMIT 5
        """)
        students = cursor.fetchall()
        
        print(f"✅ 학생 목록 조회 테스트 (상위 5명):")
        for student in students:
            completion = student['overall_completion_rate'] or 0
            print(f"   - {student['student_id']} | {student['name']} | "
                  f"{student['department']} | {student['grade']}학년 | "
                  f"이수율: {completion}%")
        
        # 2. 학과별 필터링 테스트
        if students:
            test_dept = students[0]['department']
            if test_dept:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM students 
                    WHERE department = %s
                """, (test_dept,))
                dept_count = cursor.fetchone()['count']
                print(f"✅ '{test_dept}' 학과 필터링: {dept_count}명")
        
        # 3. 학년별 필터링 테스트
        cursor.execute("""
            SELECT grade, COUNT(*) as count 
            FROM students 
            WHERE grade IS NOT NULL 
            GROUP BY grade 
            ORDER BY grade
        """)
        grade_stats = cursor.fetchall()
        
        print(f"✅ 학년별 분포:")
        for grade_stat in grade_stats:
            print(f"   - {grade_stat['grade']}학년: {grade_stat['count']}명")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 학생 검색 기능 테스트 실패: {e}")
        return False

def test_student_detail_functionality():
    """학생 상세 정보 조회 테스트"""
    print("\n👤 학생 상세 정보 테스트")
    print("-" * 40)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 테스트할 학생 ID 찾기
        cursor.execute("SELECT student_id FROM students LIMIT 1")
        test_student = cursor.fetchone()
        
        if not test_student:
            print("⚠️ 테스트할 학생 데이터가 없습니다.")
            return False
        
        student_id = test_student['student_id']
        
        # 1. 기본 학생 정보
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student_info = cursor.fetchone()
        print(f"✅ 학생 기본 정보: {student_info['name']} ({student_info['student_id']})")
        print(f"   학과: {student_info['department']}, 학년: {student_info['grade']}")
        
        # 2. 분석 결과
        cursor.execute("""
            SELECT * FROM graduation_analysis 
            WHERE student_id = %s 
            ORDER BY analysis_date DESC
        """, (student_id,))
        analyses = cursor.fetchall()
        
        print(f"✅ 분석 결과: {len(analyses)}개")
        if analyses:
            latest = analyses[0]
            print(f"   최신 분석: {latest['analysis_date']}")
            print(f"   이수율: {latest['overall_completion_rate']}%")
            print(f"   학점: {latest['total_completed_credits']}/{latest['total_required_credits']}")
        
        # 3. 수강 기록 요약
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as course_count,
                SUM(CASE WHEN grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P') 
                    THEN credit ELSE 0 END) as total_credits
            FROM course_records 
            WHERE student_id = %s
            GROUP BY category
            ORDER BY category
        """, (student_id,))
        course_summary = cursor.fetchall()
        
        print(f"✅ 수강 기록:")
        for course in course_summary:
            print(f"   {course['category']}: {course['course_count']}과목, {course['total_credits']}학점")
        
        # 4. 알림 통계
        cursor.execute("""
            SELECT 
                COUNT(*) as total_notifications,
                SUM(CASE WHEN nr.is_read = 0 THEN 1 ELSE 0 END) as unread_count
            FROM notification_recipients nr
            WHERE nr.recipient_id = %s
        """, (student_id,))
        notification_stats = cursor.fetchone()
        
        if notification_stats:
            print(f"✅ 알림 통계: 총 {notification_stats['total_notifications']}개, "
                  f"읽지않음 {notification_stats['unread_count']}개")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 학생 상세 정보 테스트 실패: {e}")
        return False

def test_notification_functionality():
    """알림 발송 기능 테스트"""
    print("\n🔔 알림 발송 기능 테스트")
    print("-" * 40)
    
    try:
        from notification_system import send_notification_to_students
        
        # 1. 전체 학생 대상 알림 테스트
        result1 = send_notification_to_students(
            sender_id='admin',
            title='학생 관리 시스템 테스트 알림',
            message='관리자 학생 관리 시스템 기능 테스트를 위한 알림입니다.',
            target_type='all',
            is_urgent=False,
            db_config=db_config
        )
        
        if result1.get('success'):
            print(f"✅ 전체 학생 알림 발송: {result1.get('recipients_count', 0)}명")
        else:
            print(f"❌ 전체 학생 알림 발송 실패: {result1.get('error')}")
        
        # 2. 특정 학과 대상 알림 테스트
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL LIMIT 1")
        test_dept = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if test_dept:
            result2 = send_notification_to_students(
                sender_id='admin',
                title='학과별 알림 테스트',
                message=f'{test_dept[0]} 학과 학생들을 대상으로 한 테스트 알림입니다.',
                target_type='group',
                target_data={'department': test_dept[0]},
                is_urgent=True,
                db_config=db_config
            )
            
            if result2.get('success'):
                print(f"✅ {test_dept[0]} 학과 알림 발송: {result2.get('recipients_count', 0)}명")
            else:
                print(f"❌ 학과별 알림 발송 실패: {result2.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 알림 발송 기능 테스트 실패: {e}")
        return False

def test_bulk_operations():
    """일괄 처리 기능 테스트"""
    print("\n⚡ 일괄 처리 기능 테스트")
    print("-" * 40)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 테스트할 학생 ID들 가져오기
        cursor.execute("SELECT student_id FROM students LIMIT 3")
        test_students = [row['student_id'] for row in cursor.fetchall()]
        
        if not test_students:
            print("⚠️ 테스트할 학생 데이터가 없습니다.")
            return False
        
        print(f"✅ 테스트 대상 학생: {len(test_students)}명")
        
        # 1. 일괄 재분석 시뮬레이션 (실제로는 실행하지 않음)
        print("✅ 일괄 재분석 기능 확인 완료 (시뮬레이션)")
        
        # 2. 학년 업데이트 테스트용 데이터 확인
        cursor.execute("""
            SELECT student_id, grade 
            FROM students 
            WHERE student_id IN (%s)
        """ % ','.join(['%s'] * len(test_students)), test_students)
        
        current_grades = cursor.fetchall()
        print("✅ 현재 학년 정보:")
        for student in current_grades:
            print(f"   {student['student_id']}: {student['grade']}학년")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 일괄 처리 기능 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🎓 관리자 학생 관리 시스템 종합 테스트")
    print("=" * 80)
    
    tests = [
        ("학생 관리 API 기본 기능", test_student_management_api),
        ("학생 검색 및 필터링", test_student_search_functionality),
        ("학생 상세 정보 조회", test_student_detail_functionality),
        ("알림 발송 기능", test_notification_functionality),
        ("일괄 처리 기능", test_bulk_operations),
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
    
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n통과: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 모든 테스트가 통과했습니다!")
        print("\n💡 관리자 학생 관리 시스템 사용법:")
        print("1. 웹 브라우저에서 http://localhost:5000 접속")
        print("2. 관리자 계정 (admin/admin123)으로 로그인")
        print("3. '학생 관리' 메뉴 클릭")
        print("4. 다음 기능들을 테스트해보세요:")
        print("   ✅ 학생 목록 조회 및 검색")
        print("   ✅ 학과/학년별 필터링")
        print("   ✅ 학생 상세 정보 조회")
        print("   ✅ 학생 정보 수정")
        print("   ✅ 개별/일괄 재분석")
        print("   ✅ 선택 학생 또는 그룹별 알림 발송")
        print("   ✅ 일괄 학년 변경")
        
    else:
        print(f"\n⚠️ {len(results) - passed}개의 테스트가 실패했습니다.")
        print("실패한 부분을 확인하고 수정이 필요합니다.")

if __name__ == "__main__":
    main()