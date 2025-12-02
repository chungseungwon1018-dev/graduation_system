#!/usr/bin/env python3
"""
학생 목록 문제 해결 스크립트
"""

import os
import sys

def create_test_html():
    """테스트용 HTML 파일 생성"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>학생 목록 테스트</title>
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
        <h3>1️⃣ 서버 상태 확인</h3>
        <button onclick="checkServer()">서버 상태 확인</button>
        <div id="serverStatus"></div>
    </div>
    
    <div class="section">
        <h3>2️⃣ 로그인 상태 확인</h3>
        <button onclick="checkLogin()">로그인 상태 확인</button>
        <button onclick="adminLogin()">관리자 로그인</button>
        <div id="loginStatus"></div>
    </div>
    
    <div class="section">
        <h3>3️⃣ API 직접 테스트</h3>
        <button onclick="testStudentAPI()">학생 API 호출</button>
        <button onclick="testWithDebug()">디버그 모드 API 호출</button>
        <div id="apiStatus"></div>
    </div>
    
    <div class="section">
        <h3>4️⃣ 해결 방안</h3>
        <div id="solutions">
            <h4>🔧 해결 방법들:</h4>
            <ol>
                <li><strong>서버 재시작:</strong> Flask 서버를 다시 시작해보세요</li>
                <li><strong>브라우저 캐시 삭제:</strong> Ctrl+F5로 강력 새로고침</li>
                <li><strong>인증 상태 확인:</strong> 다시 로그인 해보세요</li>
                <li><strong>네트워크 연결:</strong> 데이터베이스 서버 연결 상태 확인</li>
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
        
        async function checkServer() {
            const statusDiv = document.getElementById('serverStatus');
            statusDiv.innerHTML = '<div class="info">서버 상태 확인 중...</div>';
            log('서버 상태 확인 시작');
            
            try {
                const response = await fetch('/');
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="success">✅ 서버가 정상 작동 중입니다</div>';
                    log('서버 상태: 정상', 'success');
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ 서버 응답 오류: ${response.status}</div>`;
                    log(`서버 오류: HTTP ${response.status}`, 'error');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">❌ 서버 연결 실패: ${error.message}</div>`;
                log(`서버 연결 실패: ${error.message}`, 'error');
            }
        }
        
        async function checkLogin() {
            const statusDiv = document.getElementById('loginStatus');
            statusDiv.innerHTML = '<div class="info">로그인 상태 확인 중...</div>';
            log('로그인 상태 확인 시작');
            
            try {
                const response = await fetch('/admin/dashboard');
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="success">✅ 관리자로 로그인된 상태입니다</div>';
                    log('로그인 상태: 관리자 로그인됨', 'success');
                } else if (response.status === 302 || response.redirected) {
                    statusDiv.innerHTML = '<div class="error">❌ 로그인이 필요합니다</div>';
                    log('로그인 상태: 로그인 필요', 'error');
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ 인증 오류: ${response.status}</div>`;
                    log(`인증 오류: HTTP ${response.status}`, 'error');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">❌ 확인 실패: ${error.message}</div>`;
                log(`로그인 상태 확인 실패: ${error.message}`, 'error');
            }
        }
        
        async function adminLogin() {
            const statusDiv = document.getElementById('loginStatus');
            statusDiv.innerHTML = '<div class="info">관리자 로그인 중...</div>';
            log('관리자 로그인 시도');
            
            try {
                const formData = new FormData();
                formData.append('username', 'admin');
                formData.append('password', 'admin123');
                
                const response = await fetch('/login', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    statusDiv.innerHTML = '<div class="success">✅ 관리자 로그인 성공</div>';
                    log('관리자 로그인 성공', 'success');
                    
                    // 로그인 후 자동으로 상태 재확인
                    setTimeout(checkLogin, 1000);
                } else {
                    statusDiv.innerHTML = `<div class="error">❌ 로그인 실패: ${response.status}</div>`;
                    log(`로그인 실패: HTTP ${response.status}`, 'error');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">❌ 로그인 오류: ${error.message}</div>`;
                log(`로그인 오류: ${error.message}`, 'error');
            }
        }
        
        async function testStudentAPI() {
            const statusDiv = document.getElementById('apiStatus');
            statusDiv.innerHTML = '<div class="info">학생 API 호출 중...</div>';
            log('학생 API 호출 시작');
            
            try {
                const response = await fetch('/api/admin/students?page=1&limit=10');
                
                log(`API 응답 상태: ${response.status}`);
                log(`API 응답 헤더: ${JSON.stringify([...response.headers.entries()])}`);
                
                if (response.ok) {
                    const data = await response.json();
                    log(`API 응답 데이터: ${JSON.stringify(data, null, 2)}`);
                    
                    if (data.success) {
                        const students = data.students || [];
                        let resultHTML = `<div class="success">✅ 학생 API 호출 성공<br>`;
                        resultHTML += `총 학생 수: ${data.total}<br>`;
                        resultHTML += `조회된 학생: ${students.length}명<br>`;
                        
                        if (students.length > 0) {
                            resultHTML += `<br><strong>학생 목록:</strong><br>`;
                            students.slice(0, 5).forEach(student => {
                                resultHTML += `• ${student.student_id} | ${student.name || '이름없음'} | ${student.department || '학과없음'}<br>`;
                            });
                        }
                        resultHTML += `</div>`;
                        
                        statusDiv.innerHTML = resultHTML;
                        log('학생 API 호출 성공', 'success');
                    } else {
                        statusDiv.innerHTML = `<div class="error">❌ API 오류: ${data.error}</div>`;
                        log(`API 오류: ${data.error}`, 'error');
                    }
                } else {
                    const errorText = await response.text();
                    statusDiv.innerHTML = `<div class="error">❌ API 호출 실패<br>상태: ${response.status}<br>응답: ${errorText.substring(0, 200)}...</div>`;
                    log(`API 호출 실패: ${response.status} - ${errorText}`, 'error');
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">❌ API 호출 오류: ${error.message}</div>`;
                log(`API 호출 오류: ${error.message}`, 'error');
            }
        }
        
        async function testWithDebug() {
            log('디버그 모드 API 호출 시작');
            
            // 먼저 로그인 상태 확인
            await checkLogin();
            
            // 잠시 후 API 호출
            setTimeout(async () => {
                await testStudentAPI();
            }, 1000);
        }
        
        // 페이지 로드 시 자동 실행
        window.addEventListener('load', function() {
            log('페이지 로드 완료');
            log('자동 진단 시작...');
            
            setTimeout(async () => {
                await checkServer();
                setTimeout(async () => {
                    await checkLogin();
                }, 1000);
            }, 500);
        });
    </script>
</body>
</html>
    """
    
    with open('student_list_debug.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ 테스트 HTML 파일이 생성되었습니다: student_list_debug.html")

def create_simple_flask_app():
    """간단한 Flask 앱 생성"""
    app_content = '''#!/usr/bin/env python3
"""
학생 목록 문제 해결용 간단한 Flask 앱
"""

from flask import Flask, jsonify, render_template, request, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'debug-secret-key'

@app.route('/')
def index():
    return redirect('/debug')

@app.route('/debug')
def debug_page():
    """디버그 페이지"""
    with open('student_list_debug.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """간단한 로그인"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 'admin'
            session['role'] = 'admin'
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '로그인 정보가 올바르지 않습니다'}), 401
    
    return "로그인 페이지"

@app.route('/admin/dashboard')
def admin_dashboard():
    """관리자 대시보드"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    return "관리자 대시보드"

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
        }
    ]
    
    return jsonify({
        'success': True,
        'students': test_students,
        'total': len(test_students),
        'page': 1,
        'limit': 10,
        'departments': ['컴퓨터공학과', '소프트웨어학과']
    })

if __name__ == '__main__':
    print("🔧 학생 목록 문제 해결용 서버 시작")
    print("브라우저에서 http://localhost:5001/debug 접속하세요")
    app.run(debug=True, host='0.0.0.0', port=5001)
'''
    
    with open('debug_server.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    
    print("✅ 디버그 서버 파일이 생성되었습니다: debug_server.py")

def show_instructions():
    """해결 방법 안내"""
    print("\n" + "="*60)
    print("🔍 학생 목록 문제 해결 가이드")
    print("="*60)
    
    print("\n1️⃣ 즉시 해결 방법:")
    print("   • python debug_server.py 실행")
    print("   • 브라우저에서 http://localhost:5001/debug 접속")
    print("   • 단계별 진단 수행")
    
    print("\n2️⃣ 원본 서버 문제 해결:")
    print("   • 데이터베이스 연결 상태 확인")
    print("   • Flask 서버 재시작: python main_app.py")
    print("   • 브라우저 캐시 삭제 (Ctrl+F5)")
    
    print("\n3️⃣ 일반적인 해결책:")
    print("   • 관리자 계정 재로그인 (admin/admin123)")
    print("   • 브라우저 개발자 도구(F12)에서 네트워크 탭 확인")
    print("   • API 응답 상태 코드 확인")
    
    print("\n4️⃣ 추가 디버깅:")
    print("   • student_list_debug.html 파일을 브라우저에서 직접 열기")
    print("   • 서버 로그 확인")
    print("   • 네트워크 연결 상태 확인")

if __name__ == "__main__":
    print("🛠️ 학생 목록 문제 해결 스크립트")
    print("="*50)
    
    # 1. 테스트 HTML 파일 생성
    create_test_html()
    
    # 2. 디버그 서버 생성
    create_simple_flask_app()
    
    # 3. 해결 방법 안내
    show_instructions()
    
    print("\n✅ 모든 파일이 생성되었습니다!")
    print("\n🚀 다음 명령어로 디버그 서버를 시작하세요:")
    print("   python debug_server.py")
'''