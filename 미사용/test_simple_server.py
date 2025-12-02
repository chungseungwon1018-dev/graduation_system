#!/usr/bin/env python3
"""
간단한 테스트 서버로 학생 목록 문제 진단
"""

from flask import Flask, jsonify, render_template_string
import mysql.connector
from mysql.connector import Error
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'test-secret-key'

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>학생 목록 문제 진단</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            .success { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
            button { padding: 10px 20px; margin: 5px; }
        </style>
    </head>
    <body>
        <h1>🔍 학생 목록 문제 진단</h1>
        
        <div class="test-section">
            <h3>1. 데이터베이스 연결 테스트</h3>
            <button onclick="testDatabase()">DB 연결 테스트</button>
            <div id="dbResult"></div>
        </div>
        
        <div class="test-section">
            <h3>2. 학생 API 테스트</h3>
            <button onclick="testStudentAPI()">학생 API 호출</button>
            <div id="apiResult"></div>
        </div>
        
        <div class="test-section">
            <h3>3. 학생 데이터 확인</h3>
            <button onclick="checkStudentData()">학생 데이터 확인</button>
            <div id="dataResult"></div>
        </div>

        <script>
        async function testDatabase() {
            const result = document.getElementById('dbResult');
            result.innerHTML = '테스트 중...';
            
            try {
                const response = await fetch('/test-db');
                const data = await response.json();
                
                if (data.success) {
                    result.innerHTML = `<div class="success">✅ DB 연결 성공: ${data.message}</div>`;
                } else {
                    result.innerHTML = `<div class="error">❌ DB 연결 실패: ${data.error}</div>`;
                }
            } catch (error) {
                result.innerHTML = `<div class="error">❌ 오류: ${error.message}</div>`;
            }
        }
        
        async function testStudentAPI() {
            const result = document.getElementById('apiResult');
            result.innerHTML = '테스트 중...';
            
            try {
                const response = await fetch('/api/students');
                const data = await response.json();
                
                if (data.success) {
                    result.innerHTML = `<div class="success">✅ API 호출 성공: ${data.students.length}명의 학생</div>`;
                } else {
                    result.innerHTML = `<div class="error">❌ API 호출 실패: ${data.error}</div>`;
                }
            } catch (error) {
                result.innerHTML = `<div class="error">❌ 오류: ${error.message}</div>`;
            }
        }
        
        async function checkStudentData() {
            const result = document.getElementById('dataResult');
            result.innerHTML = '확인 중...';
            
            try {
                const response = await fetch('/check-data');
                const data = await response.json();
                
                if (data.success) {
                    let html = `<div class="success">✅ 데이터 확인 완료<br>`;
                    html += `총 학생 수: ${data.total_students}<br>`;
                    html += `분석 완료: ${data.analyzed_students}<br>`;
                    html += `학과 수: ${data.departments.length}<br>`;
                    html += `학과 목록: ${data.departments.join(', ')}</div>`;
                    result.innerHTML = html;
                } else {
                    result.innerHTML = `<div class="error">❌ 데이터 확인 실패: ${data.error}</div>`;
                }
            } catch (error) {
                result.innerHTML = `<div class="error">❌ 오류: ${error.message}</div>`;
            }
        }
        </script>
    </body>
    </html>
    """

@app.route('/test-db')
def test_db():
    """데이터베이스 연결 테스트"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'message': '데이터베이스 연결 성공'})
    except Error as e:
        logger.error(f"DB 연결 오류: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/students')
def get_students():
    """학생 목록 조회 API"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
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
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'students': students,
            'total': len(students)
        })
        
    except Exception as e:
        logger.error(f"학생 목록 조회 오류: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/check-data')
def check_data():
    """데이터 상태 확인"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 총 학생 수
        cursor.execute("SELECT COUNT(*) as count FROM students")
        total_students = cursor.fetchone()['count']
        
        # 분석 완료된 학생 수
        cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM graduation_analysis")
        analyzed_students = cursor.fetchone()['count']
        
        # 학과 목록
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL ORDER BY department")
        departments = [row['department'] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'total_students': total_students,
            'analyzed_students': analyzed_students,
            'departments': departments
        })
        
    except Exception as e:
        logger.error(f"데이터 확인 오류: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🔍 진단용 테스트 서버 시작")
    print("브라우저에서 http://localhost:8000 접속하세요")
    app.run(debug=True, host='0.0.0.0', port=8000)