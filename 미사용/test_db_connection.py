#!/usr/bin/env python3
"""
데이터베이스 연결 직접 테스트
"""

import mysql.connector
from mysql.connector import Error
import json

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def test_connection():
    """데이터베이스 연결 테스트"""
    print("🔗 데이터베이스 연결 테스트")
    print("=" * 50)
    
    try:
        print(f"연결 정보: {db_config['host']}:{db_config['port']}")
        print(f"데이터베이스: {db_config['database']}")
        print(f"사용자: {db_config['user']}")
        
        connection = mysql.connector.connect(**db_config)
        print("✅ 데이터베이스 연결 성공")
        
        cursor = connection.cursor(dictionary=True)
        
        # 기본 테스트 쿼리
        cursor.execute("SELECT VERSION() as version")
        version = cursor.fetchone()
        print(f"MySQL 버전: {version['version']}")
        
        # 테이블 존재 확인
        cursor.execute("SHOW TABLES")
        tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
        print(f"테이블 목록: {tables}")
        
        # 학생 테이블 확인
        if 'students' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM students")
            student_count = cursor.fetchone()['count']
            print(f"✅ 학생 수: {student_count}명")
            
            # 샘플 학생 데이터
            cursor.execute("SELECT * FROM students LIMIT 3")
            students = cursor.fetchall()
            print("✅ 샘플 학생 데이터:")
            for student in students:
                print(f"   - {student['student_id']}: {student.get('name', '이름없음')} ({student.get('department', '학과없음')})")
        else:
            print("❌ students 테이블이 없습니다")
        
        # 분석 테이블 확인
        if 'graduation_analysis' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM graduation_analysis")
            analysis_count = cursor.fetchone()['count']
            print(f"✅ 분석 데이터: {analysis_count}개")
        else:
            print("❌ graduation_analysis 테이블이 없습니다")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        return False

def test_student_query():
    """학생 목록 쿼리 테스트"""
    print("\n📋 학생 목록 쿼리 테스트")
    print("-" * 40)
    
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 학생 관리 API와 동일한 쿼리 실행
        query = """
        SELECT s.*, 
               ga.overall_completion_rate,
               ga.total_completed_credits,
               ga.total_required_credits,
               ga.analysis_date
        FROM students s
        LEFT JOIN graduation_analysis ga ON s.student_id = ga.student_id
        ORDER BY s.student_id 
        LIMIT 10
        """
        
        cursor.execute(query)
        students = cursor.fetchall()
        
        print(f"✅ 조회된 학생 수: {len(students)}명")
        
        if students:
            print("학생 목록:")
            for i, student in enumerate(students, 1):
                completion_rate = student.get('overall_completion_rate', 0) or 0
                print(f"   {i}. {student['student_id']} | {student.get('name', '이름없음')} | "
                      f"{student.get('department', '학과없음')} | {student.get('grade', '학년없음')}학년 | "
                      f"이수율: {completion_rate}%")
        
        # 학과 목록 조회
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL ORDER BY department")
        departments = [row['department'] for row in cursor.fetchall()]
        print(f"✅ 학과 목록: {departments}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 학생 쿼리 오류: {e}")
        return False

if __name__ == "__main__":
    print("🔍 학생 목록 문제 진단")
    print("=" * 60)
    
    # 1. 데이터베이스 연결 테스트
    db_ok = test_connection()
    
    if db_ok:
        # 2. 학생 쿼리 테스트
        query_ok = test_student_query()
        
        if query_ok:
            print("\n✅ 모든 테스트 통과!")
            print("\n💡 다음 단계:")
            print("1. Flask 서버를 다시 시작해보세요")
            print("2. 브라우저에서 관리자로 로그인 후 학생 관리 페이지 접속")
            print("3. 개발자 도구(F12)에서 네트워크 탭을 확인하여 API 요청 상태 점검")
        else:
            print("\n❌ 학생 쿼리에 문제가 있습니다")
    else:
        print("\n❌ 데이터베이스 연결에 문제가 있습니다")
        print("네트워크 상태와 데이터베이스 서버 상태를 확인해주세요")