#!/usr/bin/env python3
"""
학생 목록 문제 해결용 간단한 Flask 앱
"""

from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'debug-secret-key'

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>학생 목록 문제 진단</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #d1ecf1; color: #0c5460; }
        button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .log { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
    </style>
</head>
<body>
    <h1>🔍 학생 목록 문제 진단 및 해결</h1>
    
    <div class="section info">
        <h3>📋 현재 상황</h3>
        <p>관리자 학생 관리 페이지에서 "학생 목록을 불러올 수 없는 문제"가 발생했습니다.</p>
        <p>이 페이지에서 단계별로 문제를 진단하고 해결해보겠습니다.</p>
    </div>
    
    <div class="section">
        <h3>1️⃣ 로그인 테스트</h3>
        <button onclick="adminLogin()">관리자 로그인 테스트</button>
        <div id="loginStatus"></div>
    </div>
    
    <div class="section">
        <h3>2️⃣ API 테스트</h3>
        <button onclick="testStudentAPI()">학생 API 호출 테스트</button>
        <div id="apiStatus"></div>
    </div>
    
    <div class="section">
        <h3>3️⃣ 해결 방안</h3>
        <div class="info">
            <h4>🔧 해결 방법들:</h4>
            <ol>
                <li><strong>원본 서버 재시작:</strong> main_app.py를 다시 실행</li>
                <li><strong>브라우저 캐시 삭제:</strong> Ctrl+F5로 강력 새로고침</li>
                <li><strong>데이터베이스 연결 확인:</strong> 네트워크 상태 점검</li>
                <li><strong>인증 상태 재설정:</strong> 로그아웃 후 재로그인</li>
            </ol>
        </div>
    </div>
    
    <div class="section">
        <h3>📝 디버그 로그</h3>
        <button onclick="clearLog()">로그 지우기</button>
        <div id="debugLog" class="log"></div>
    </div>

    <script>
        function log(message, type = 'info') {
            const logDiv = document.getElementById('debugLog');
            const timestamp = new Date().toLocaleTimeString();
            const logClass = type === 'error' ? 'color: red' : type === 'success' ? 'color: green' : 'color: blue';
            logDiv.innerHTML += `<div style="${logClass}">[${timestamp}] ${message}</div>`;
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('debugLog').innerHTML = '';
        }
        
        async function adminLogin() {
            const statusDiv = document.getElementById('loginStatus');
            statusDiv.innerHTML = '<div class="info">관리자 로그인 테스트 중...</div>';
            log('관리자 로그인 테스트 시작');
            
            try {
                const formData = new FormData();
                formData.append('username', 'admin');
                formData.append('password', 'admin123');
                
                const response = await fetch('/login', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="success">✅ 로그인 테스트 성공</div>';
                    log('로그인 테스트 성공', 'success');
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ 로그인 테스트 실패: ${response.status}</div>`;
                    log(`로그인 테스트 실패: ${response.status}`, 'error');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">❌ 로그인 오류: ${error.message}</div>`;
                log(`로그인 오류: ${error.message}`, 'error');
            }
        }
        
        async function testStudentAPI() {
            const statusDiv = document.getElementById('apiStatus');
            statusDiv.innerHTML = '<div class="info">학생 API 테스트 중...</div>';
            log('학생 API 테스트 시작');
            
            try {
                const response = await fetch('/api/admin/students?page=1&limit=5');
                
                if (response.ok) {
                    const data = await response.json();
                    
                    if (data.success) {
                        const students = data.students || [];
                        let resultHTML = `<div class="success">✅ 학생 API 테스트 성공<br>`;
                        resultHTML += `총 학생 수: ${data.total}<br>`;
                        resultHTML += `조회된 학생: ${students.length}명<br>`;
                        
                        if (students.length > 0) {
                            resultHTML += `<br><strong>테스트 학생 목록:</strong><br>`;
                            students.forEach(student => {
                                resultHTML += `• ${student.student_id} | ${student.name} | ${student.department} | 이수율: ${student.overall_completion_rate}%<br>`;
                            });
                        }
                        resultHTML += `</div>`;
                        
                        statusDiv.innerHTML = resultHTML;
                        log('학생 API 테스트 성공', 'success');
                    } else {
                        statusDiv.innerHTML = `<div class="error">❌ API 오류: ${data.error}</div>`;
                        log(`API 오류: ${data.error}`, 'error');
                    }
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ API 호출 실패: ${response.status}</div>`;
                    log(`API 호출 실패: ${response.status}`, 'error');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">❌ API 호출 오류: ${error.message}</div>`;
                log(`API 호출 오류: ${error.message}`, 'error');
            }
        }
        
        // 페이지 로드 시 자동 실행
        window.addEventListener('load', function() {
            log('진단 페이지 로드 완료');
        });
    </script>
</body>
</html>
    '''

@app.route('/login', methods=['POST'])
def login():
    """간단한 로그인 테스트"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'admin123':
        session['user_id'] = 'admin'
        session['role'] = 'admin'
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': '로그인 정보가 올바르지 않습니다'}), 401

@app.route('/api/admin/students')
def get_students():
    """학생 목록 API (테스트용)"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
    
    # 테스트 데이터
    test_students = [
        {
            'student_id': '2021026018',
            'name': '테스트 학생1',
            'department': '컴퓨터공학과',
            'grade': 3,
            'overall_completion_rate': 75.5,
            'total_completed_credits': 90,
            'total_required_credits': 120,
            'analysis_date': '2024-12-02'
        },
        {
            'student_id': '2021026019',
            'name': '테스트 학생2',
            'department': '소프트웨어학과',
            'grade': 2,
            'overall_completion_rate': 60.0,
            'total_completed_credits': 72,
            'total_required_credits': 120,
            'analysis_date': '2024-12-01'
        },
        {
            'student_id': '2020123456',
            'name': '테스트 학생3',
            'department': '전자공학과',
            'grade': 4,
            'overall_completion_rate': 95.0,
            'total_completed_credits': 114,
            'total_required_credits': 120,
            'analysis_date': '2024-12-01'
        }
    ]
    
    return jsonify({
        'success': True,
        'students': test_students,
        'total': len(test_students),
        'page': 1,
        'limit': 10,
        'departments': ['컴퓨터공학과', '소프트웨어학과', '전자공학과']
    })

if __name__ == '__main__':
    print("🔧 학생 목록 문제 해결용 디버그 서버 시작")
    print("=" * 50)
    print("브라우저에서 다음 URL로 접속하세요:")
    print("👉 http://localhost:5001")
    print("=" * 50)
    print("이 서버는 학생 목록 문제를 진단하고 해결하는 도구입니다.")
    print("실제 데이터베이스 연결 없이 테스트할 수 있습니다.")
    app.run(debug=True, host='0.0.0.0', port=5001)