from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import bcrypt
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import secrets
import hashlib
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # 실제 운영에서는 환경변수로 설정

class AuthSystem:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.session_timeout = timedelta(hours=8)  # 8시간 세션 유지
    
    def connect_db(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            logger.info("MySQL 데이터베이스 연결 성공")
        except Error as e:
            logger.error(f"MySQL 연결 오류: {e}")
            raise
    
    def disconnect_db(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL 연결 해제")
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, password: str, role: str = 'student') -> Dict:
        """사용자 계정 생성"""
        try:
            cursor = self.connection.cursor()
            
            # 중복 사용자 확인
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return {"success": False, "error": "이미 존재하는 사용자 ID입니다."}
            
            # 비밀번호 해시화
            hashed_password = self.hash_password(password)
            
            # 사용자 생성
            query = """
            INSERT INTO users (username, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (username, hashed_password, role, True))
            self.connection.commit()
            cursor.close()
            
            logger.info(f"사용자 생성 완료: {username} ({role})")
            
            return {"success": True, "message": "사용자가 생성되었습니다."}
            
        except Error as e:
            self.connection.rollback()
            logger.error(f"사용자 생성 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """사용자 인증"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT username, password_hash, role, is_active 
            FROM users 
            WHERE username = %s
            """
            
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "error": "존재하지 않는 사용자 ID입니다."}
            
            if not user['is_active']:
                return {"success": False, "error": "비활성화된 계정입니다."}
            
            if not self.verify_password(password, user['password_hash']):
                return {"success": False, "error": "비밀번호가 올바르지 않습니다."}
            
            # 마지막 로그인 시간 업데이트
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE username = %s", 
                (username,)
            )
            self.connection.commit()
            cursor.close()
            
            logger.info(f"사용자 로그인: {username} ({user['role']})")
            
            return {
                "success": True,
                "user": {
                    "username": user['username'],
                    "role": user['role']
                }
            }
            
        except Error as e:
            logger.error(f"사용자 인증 오류: {e}")
            return {"success": False, "error": "인증 중 오류가 발생했습니다."}
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """세션 생성"""
        try:
            cursor = self.connection.cursor()
            
            # 기존 세션 정리
            self.cleanup_expired_sessions()
            
            # 새 세션 ID 생성
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + self.session_timeout
            
            query = """
            INSERT INTO user_sessions (id, user_id, ip_address, user_agent, 
                                     last_activity, expires_at, created_at)
            VALUES (%s, %s, %s, %s, NOW(), %s, NOW())
            """
            
            cursor.execute(query, (session_id, user_id, ip_address, user_agent, expires_at))
            self.connection.commit()
            cursor.close()
            
            return session_id
            
        except Error as e:
            logger.error(f"세션 생성 오류: {e}")
            return None
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """세션 유효성 검증"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT s.user_id, s.expires_at, u.role, u.is_active
            FROM user_sessions s
            JOIN users u ON s.user_id = u.username
            WHERE s.id = %s AND s.expires_at > NOW()
            """
            
            cursor.execute(query, (session_id,))
            session = cursor.fetchone()
            
            if session and session['is_active']:
                # 세션 활동 시간 업데이트
                cursor.execute(
                    "UPDATE user_sessions SET last_activity = NOW() WHERE id = %s",
                    (session_id,)
                )
                self.connection.commit()
                cursor.close()
                
                return {
                    "user_id": session['user_id'],
                    "role": session['role']
                }
            
            cursor.close()
            return None
            
        except Error as e:
            logger.error(f"세션 검증 오류: {e}")
            return None
    
    def destroy_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE id = %s", (session_id,))
            self.connection.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        except Error as e:
            logger.error(f"세션 삭제 오류: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE expires_at < NOW()")
            deleted_count = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            if deleted_count > 0:
                logger.info(f"만료된 세션 {deleted_count}개 정리 완료")
                
        except Error as e:
            logger.error(f"세션 정리 오류: {e}")
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Dict:
        """비밀번호 변경"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 현재 비밀번호 확인
            cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if not user or not self.verify_password(old_password, user['password_hash']):
                return {"success": False, "error": "현재 비밀번호가 올바르지 않습니다."}
            
            # 새 비밀번호 해시화 및 업데이트
            new_hashed = self.hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE username = %s",
                (new_hashed, username)
            )
            self.connection.commit()
            cursor.close()
            
            logger.info(f"비밀번호 변경 완료: {username}")
            
            return {"success": True, "message": "비밀번호가 변경되었습니다."}
            
        except Error as e:
            logger.error(f"비밀번호 변경 오류: {e}")
            return {"success": False, "error": "비밀번호 변경 중 오류가 발생했습니다."}

# Flask 앱에서 사용할 인증 시스템 인스턴스
auth_system = AuthSystem({
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
})

def login_required(f):
    """로그인 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            return redirect(url_for('login'))
        
        auth_system.connect_db()
        try:
            session_data = auth_system.validate_session(session['session_id'])
            if not session_data:
                session.clear()
                return redirect(url_for('login'))
            
            # 요청에 사용자 정보 추가
            request.user = session_data
            return f(*args, **kwargs)
        finally:
            auth_system.disconnect_db()
    
    return decorated_function

def admin_required(f):
    """관리자 권한 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            return redirect(url_for('login'))
        
        auth_system.connect_db()
        try:
            session_data = auth_system.validate_session(session['session_id'])
            if not session_data or session_data['role'] != 'admin':
                flash('관리자 권한이 필요합니다.', 'error')
                return redirect(url_for('dashboard'))
            
            request.user = session_data
            return f(*args, **kwargs)
        finally:
            auth_system.disconnect_db()
    
    return decorated_function

@app.route('/')
def index():
    if 'session_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        flash('사용자 ID와 비밀번호를 입력해주세요.', 'error')
        return render_template('login.html')
    
    auth_system.connect_db()
    try:
        auth_result = auth_system.authenticate_user(username, password)
        
        if auth_result['success']:
            # 세션 생성
            session_id = auth_system.create_session(
                username,
                request.remote_addr,
                request.headers.get('User-Agent', '')
            )
            
            if session_id:
                session['session_id'] = session_id
                session['user_id'] = username
                session['role'] = auth_result['user']['role']
                
                logger.info(f"로그인 성공: {username}")
                
                # 역할에 따른 리다이렉트
                if auth_result['user']['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                flash('세션 생성에 실패했습니다.', 'error')
        else:
            flash(auth_result['error'], 'error')
    
    finally:
        auth_system.disconnect_db()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    name = request.form.get('name', '').strip()
    is_admin = request.form.get('is_admin') == 'on'
    
    # 입력 검증
    if not all([username, password, confirm_password, name]):
        flash('모든 필드를 입력해주세요.', 'error')
        return render_template('register.html')
    
    if password != confirm_password:
        flash('비밀번호가 일치하지 않습니다.', 'error')
        return render_template('register.html')
    
    if len(password) < 6:
        flash('비밀번호는 최소 6자 이상이어야 합니다.', 'error')
        return render_template('register.html')
    
    auth_system.connect_db()
    try:
        role = 'admin' if is_admin else 'student'
        result = auth_system.create_user(username, password, role)
        
        if result['success']:
            flash('계정이 생성되었습니다. 로그인해주세요.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result['error'], 'error')
    
    finally:
        auth_system.disconnect_db()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'session_id' in session:
        auth_system.connect_db()
        try:
            auth_system.destroy_session(session['session_id'])
        finally:
            auth_system.disconnect_db()
    
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if request.user['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if request.user['role'] != 'student':
        return redirect(url_for('admin_dashboard'))
    return render_template('student_dashboard.html', user=request.user)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        return render_template('profile.html', user=request.user)
    
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not all([old_password, new_password, confirm_password]):
        flash('모든 필드를 입력해주세요.', 'error')
        return render_template('profile.html', user=request.user)
    
    if new_password != confirm_password:
        flash('새 비밀번호가 일치하지 않습니다.', 'error')
        return render_template('profile.html', user=request.user)
    
    if len(new_password) < 6:
        flash('새 비밀번호는 최소 6자 이상이어야 합니다.', 'error')
        return render_template('profile.html', user=request.user)
    
    auth_system.connect_db()
    try:
        result = auth_system.change_password(
            request.user['user_id'], old_password, new_password
        )
        
        if result['success']:
            flash('비밀번호가 변경되었습니다.', 'success')
        else:
            flash(result['error'], 'error')
    
    finally:
        auth_system.disconnect_db()
    
    return render_template('profile.html', user=request.user)

@app.route('/api/auth/status')
def auth_status():
    """현재 인증 상태 확인 API"""
    if 'session_id' not in session:
        return jsonify({'authenticated': False})
    
    auth_system.connect_db()
    try:
        session_data = auth_system.validate_session(session['session_id'])
        if session_data:
            return jsonify({
                'authenticated': True,
                'user': session_data
            })
        else:
            session.clear()
            return jsonify({'authenticated': False})
    finally:
        auth_system.disconnect_db()

if __name__ == '__main__':
    # 관리자 계정 생성 (초기 설정)
    auth_system.connect_db()
    try:
        result = auth_system.create_user('admin', 'admin123', 'admin')
        if result['success']:
            print("관리자 계정 생성 완료: admin / admin123")
        else:
            print(f"관리자 계정 생성 결과: {result['error']}")
    finally:
        auth_system.disconnect_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)