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
import os
from werkzeug.utils import secure_filename
import threading
from enhanced_xlsx_parser import process_excel_file_enhanced as process_excel_file
from graduation_requirements_checker import analyze_student_graduation
from graduation_requirements_checker import GraduationRequirementsChecker
from notification_system import get_user_notifications, NotificationSystem
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# 업로드 설정
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
ALLOWED_EXTENSIONS = {'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

class AuthSystem:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.session_timeout = timedelta(hours=8)
    
    def connect_db(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
        except Error as e:
            logger.error(f"MySQL 연결 오류: {e}")
            raise
    
    def disconnect_db(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username: str, password: str, role: str = 'student') -> Dict:
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return {"success": False, "error": "이미 존재하는 사용자 ID입니다."}
            
            hashed_password = self.hash_password(password)
            
            query = """
            INSERT INTO users (username, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (username, hashed_password, role, True))
            self.connection.commit()
            cursor.close()
            
            return {"success": True, "message": "사용자가 생성되었습니다."}
            
        except Error as e:
            self.connection.rollback()
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
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
            
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE username = %s", 
                (username,)
            )
            self.connection.commit()
            cursor.close()
            
            return {
                "success": True,
                "user": {
                    "username": user['username'],
                    "role": user['role']
                }
            }
            
        except Error as e:
            return {"success": False, "error": "인증 중 오류가 발생했습니다."}

auth_system = AuthSystem(db_config)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API 요청인지 확인
        is_api_request = request.path.startswith('/api/')
        
        if 'user_id' not in session:
            if is_api_request:
                return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API 요청인지 확인
        is_api_request = request.path.startswith('/api/')
        
        if 'user_id' not in session:
            if is_api_request:
                return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            if is_api_request:
                return jsonify({'success': False, 'error': '관리자 권한이 필요합니다.'}), 403
            flash('관리자 권한이 필요합니다.', 'error')
            return redirect(url_for('student_dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API 요청인지 확인
        is_api_request = request.path.startswith('/api/')
        
        if 'user_id' not in session:
            if is_api_request:
                return jsonify({'success': False, 'error': '로그인이 필요합니다.'}), 401
            return redirect(url_for('login'))
        
        if session.get('role') == 'admin':
            if not is_api_request:  # 관리자는 API는 사용할 수 있지만 학생 페이지는 접근 불가
                return redirect(url_for('admin_dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
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
            session['user_id'] = username
            session['role'] = auth_result['user']['role']
            
            if auth_result['user']['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
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
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/requirements')
@admin_required  
def admin_requirements():
    return render_template('admin_requirements.html')

@app.route('/admin/students')
@admin_required
def admin_students():
    return render_template('admin_students.html')

@app.route('/test-api')
def test_api_page():
    """API 테스트 페이지 (개발용)"""
    with open('test_browser_api.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    return render_template('student_dashboard.html', user={'user_id': session['user_id']})

# 학생 API
@app.route('/api/student/info', methods=['GET'])
@login_required
def get_student_info():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM students WHERE student_id = %s"
        cursor.execute(query, (session['user_id'],))
        student = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if student:
            return jsonify({'success': True, 'student': student})
        else:
            return jsonify({
                'success': True,
                'student': {
                    'student_id': session['user_id'],
                    'name': '정보 없음',
                    'department': '정보 없음',
                    'grade': '정보 없음',
                    'major': '정보 없음'
                }
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/analysis', methods=['GET'])
@login_required
def get_student_analysis():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT * FROM graduation_analysis 
        WHERE student_id = %s 
        ORDER BY analysis_date DESC 
        LIMIT 1
        """
        cursor.execute(query, (session['user_id'],))
        analysis = cursor.fetchone()
        
        logger.info(f"분석 데이터 조회 결과: {analysis is not None}")
        
        if analysis:
            logger.info(f"분석 데이터 상세: ID={analysis.get('id')}, 날짜={analysis.get('analysis_date')}")
            
            if analysis.get('analysis_result'):
                try:
                    analysis_data = json.loads(analysis['analysis_result'])
                    logger.info(f"JSON 파싱 성공, 요건 개수: {len(analysis_data.get('requirements_analysis', []))}")
                    
                    # 필요한 필드들이 있는지 확인
                    required_fields = ['total_completed_credits', 'total_required_credits', 'overall_completion_rate', 'requirements_analysis']
                    for field in required_fields:
                        if field not in analysis_data:
                            logger.warning(f"필수 필드 누락: {field}")
                    
                    cursor.close()
                    connection.close()
                    return jsonify({'success': True, 'analysis': analysis_data})
                except json.JSONDecodeError as je:
                    logger.error(f"JSON 파싱 오류: {je}")
                    cursor.close()
                    connection.close()
                    return jsonify({'success': False, 'error': 'JSON 파싱 오류'})
            else:
                logger.warning("analysis_result 필드가 비어있음")
        else:
            logger.info("분석 데이터 없음")
        
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'analysis': None})
        
    except Exception as e:
        logger.error(f"분석 데이터 조회 오류: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/student/profile', methods=['GET'])
@login_required
def get_student_profile():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 기본 학생 정보
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (session['user_id'],))
        student = cursor.fetchone()
        
        # 최근 분석 기록들
        cursor.execute("""
            SELECT analysis_date, overall_completion_rate, total_completed_credits, total_required_credits
            FROM graduation_analysis 
            WHERE student_id = %s 
            ORDER BY analysis_date DESC 
            LIMIT 5
        """, (session['user_id'],))
        recent_analyses = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        profile_data = {
            'basic_info': student if student else {
                'student_id': session['user_id'],
                'name': '정보 없음',
                'department': '정보 없음',
                'university': '정보 없음',
                'grade': '정보 없음',
                'major': '정보 없음',
                'minor': '정보 없음',
                'double_major': '정보 없음',
                'course_type': '정보 없음',
                'admission_date': '정보 없음',
                'curriculum_year': '정보 없음',
                'semester': '정보 없음',
                'birth_date': '정보 없음',
                'status': '정보 없음',
                'email': '정보 없음',
                'phone': '정보 없음'
            },
            'recent_analyses': recent_analyses
        }
        
        return jsonify({'success': True, 'profile': profile_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/profile/update', methods=['POST'])
@login_required
def update_student_profile():
    try:
        data = request.get_json()
        logger.info(f"받은 데이터: {data}")
        
        # 수정 가능한 필드 검증
        allowed_fields = ['phone', 'email']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        logger.info(f"필터링된 데이터: {update_data}")
        
        if not update_data:
            logger.warning("수정할 데이터가 없음")
            return jsonify({'success': False, 'error': '수정할 정보가 없습니다.'}), 400
        
        # 이메일 형식 검증
        if 'email' in update_data:
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(update_data['email']):
                logger.warning(f"잘못된 이메일 형식: {update_data['email']}")
                return jsonify({'success': False, 'error': '올바른 이메일 형식이 아닙니다.'}), 400
            logger.info(f"이메일 형식 검증 통과: {update_data['email']}")
        
        # 전화번호 형식 검증
        if 'phone' in update_data:
            phone_pattern = re.compile(r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$')
            if not phone_pattern.match(update_data['phone'].replace('-', '')):
                logger.warning(f"잘못된 전화번호 형식: {update_data['phone']}")
                return jsonify({'success': False, 'error': '올바른 전화번호 형식이 아닙니다.'}), 400
            # 하이픈 표준화
            phone = update_data['phone'].replace('-', '')
            if len(phone) == 11:
                update_data['phone'] = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
            else:
                update_data['phone'] = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
            logger.info(f"전화번호 형식 검증 통과: {update_data['phone']}")
        
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            
            # 업데이트 쿼리 생성
            query = "UPDATE students SET "
            query += ", ".join([f"{field} = %s" for field in update_data.keys()])
            query += " WHERE student_id = %s"
            
            # 파라미터 설정
            params = list(update_data.values())
            params.append(session['user_id'])
            
            logger.info(f"실행할 쿼리: {query}")
            logger.info(f"쿼리 파라미터: {params}")
            
            cursor.execute(query, params)
            connection.commit()
            
            if cursor.rowcount == 0:
                # 학생 레코드가 없는 경우, INSERT 수행
                logger.info("기존 학생 레코드가 없어 새로 생성합니다.")
                insert_query = "INSERT INTO students (student_id, phone, email) VALUES (%s, %s, %s)"
                insert_params = [session['user_id']]
                insert_params.extend([update_data.get('phone'), update_data.get('email')])
                cursor.execute(insert_query, insert_params)
                connection.commit()
            
            logger.info("데이터베이스 업데이트 성공")
            cursor.close()
            connection.close()
            
            return jsonify({
                'success': True,
                'message': '프로필이 성공적으로 업데이트되었습니다.'
            })
            
        except mysql.connector.Error as db_error:
            logger.error(f"데이터베이스 오류: {db_error}")
            return jsonify({
                'success': False,
                'error': f'데이터베이스 오류: {str(db_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"프로필 업데이트 오류: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'프로필 업데이트 중 오류가 발생했습니다: {str(e)}'
        }), 500

@app.route('/api/student/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Excel 파일(.xlsx)만 업로드 가능합니다.'}), 400

        # 파일 저장
        filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Excel 파일 처리 (parsing_warnings 포함 반환 가능)
        process_result = process_excel_file(filepath, session['user_id'], db_config)
        if isinstance(process_result, tuple):
            success, parsing_warnings = process_result
        else:
            success = process_result
            parsing_warnings = []

        if not success:
            try:
                os.remove(filepath)
            except PermissionError as pe:
                logger.warning(f"⚠️ 파일 삭제 실패 (사용 중): {filepath} - {pe}")
            except Exception as e:
                logger.warning(f"⚠️ 파일 삭제 중 기타 오류: {e}")
            return jsonify({'error': 'Excel 파일 처리에 실패했습니다.'}), 500

        # 졸업요건 분석 실행 (parsing_warnings를 전달)
        logger.info(f"졸업요건 분석 시작: {session['user_id']}")
        logger.info(f"파싱 경고: {parsing_warnings}")
        analysis_result = analyze_student_graduation(session['user_id'], db_config, parsing_warnings=parsing_warnings)
        
        if 'error' in analysis_result:
            logger.error(f"졸업요건 분석 실패: {analysis_result['error']}")
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify({'success': False, 'error': f"분석 실패: {analysis_result['error']}"}), 500
        else:
            logger.info(f"졸업요건 분석 완료: 이수율 {analysis_result.get('overall_completion_rate', 0)}%")

        # 파일 정리: 삭제 대신 보관 폴더로 이동 (잠금 이슈 회피)
        try:
            dest_name = f"processed_{filename}"
            dest_path = os.path.join(PROCESSED_FOLDER, dest_name)
            # 이미 존재하면 타임스탬프를 덧붙임
            if os.path.exists(dest_path):
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                dest_path = os.path.join(PROCESSED_FOLDER, f"{ts}_{dest_name}")
            os.replace(filepath, dest_path)
            logger.info(f"업로드 파일 이동 완료: {dest_path}")
        except PermissionError as pe:
            logger.warning(f"파일 이동 중 잠금 오류: {pe}. 백그라운드로 재시도합니다.")
            def schedule_move(src: str, dst_folder: str, retries: int = 30, interval: float = 1.0):
                import time
                for i in range(retries):
                    try:
                        if os.path.exists(src):
                            base = os.path.basename(src)
                            dp = os.path.join(dst_folder, f"processed_{base}")
                            if os.path.exists(dp):
                                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                                dp = os.path.join(dst_folder, f"{ts}_processed_{base}")
                            os.replace(src, dp)
                            logger.info(f"백그라운드 파일 이동 성공: {dp}")
                            return True
                        return True
                    except PermissionError as pe2:
                        logger.warning(f"백그라운드 이동 재시도 {i+1}/{retries}: {pe2}")
                        time.sleep(interval)
                    except Exception as e:
                        logger.warning(f"백그라운드 이동 오류: {e}")
                        return False
                logger.warning("백그라운드 이동 최종 실패")
                return False
            threading.Thread(target=schedule_move, args=(filepath, PROCESSED_FOLDER), daemon=True).start()
        except Exception as e:
            logger.warning(f"파일 이동 중 오류: {e}")

        response = {
            'success': True,
            'message': '파일 업로드 및 분석이 완료되었습니다.',
            'filename': filename,
            'analysis_summary': {
                'completion_rate': analysis_result.get('overall_completion_rate', 0),
                'completed_credits': analysis_result.get('total_completed_credits', 0),
                'required_credits': analysis_result.get('total_required_credits', 0)
            }
        }
        if parsing_warnings:
            response['parsing_warnings'] = parsing_warnings
        response['stored_file'] = os.path.join('uploads', 'processed', f"processed_{filename}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"파일 업로드 오류: {e}", exc_info=True)
        return jsonify({'error': '파일 업로드 중 오류가 발생했습니다.'}), 500

# 학생 알림 API
@app.route('/api/student/notifications', methods=['GET'])
@login_required
def get_student_notifications():
    """학생의 알림 목록 조회"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 알림 목록 조회
        query = """
        SELECT n.id, n.title, n.message, n.is_urgent, n.sent_at,
               nr.is_read, nr.read_at
        FROM notifications n
        JOIN notification_recipients nr ON n.id = nr.notification_id
        WHERE nr.recipient_id = %s
        """
        
        params = [session['user_id']]
        
        if unread_only:
            query += " AND nr.is_read = FALSE"
        
        query += " ORDER BY n.sent_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        notifications = cursor.fetchall()
        
        # 총 알림 개수 조회
        count_query = """
        SELECT COUNT(*) as total
        FROM notification_recipients nr
        WHERE nr.recipient_id = %s
        """
        count_params = [session['user_id']]
        
        if unread_only:
            count_query += " AND nr.is_read = FALSE"
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total': total,
            'has_more': offset + len(notifications) < total
        })
        
    except Exception as e:
        logger.error(f"알림 조회 오류: {e}")
        return jsonify({'success': False, 'error': '알림을 불러올 수 없습니다.'}), 500

@app.route('/api/student/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_notification_count():
    """읽지 않은 알림 개수 조회"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        query = """
        SELECT COUNT(*) as unread_count
        FROM notification_recipients nr
        WHERE nr.recipient_id = %s AND nr.is_read = FALSE
        """
        
        cursor.execute(query, (session['user_id'],))
        unread_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'unread_count': unread_count
        })
        
    except Exception as e:
        logger.error(f"읽지 않은 알림 개수 조회 오류: {e}")
        return jsonify({'success': False, 'error': '알림 개수를 조회할 수 없습니다.'}), 500

@app.route('/api/student/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    """알림을 읽음으로 표시"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 알림이 해당 사용자에게 속하는지 확인
        check_query = """
        SELECT id FROM notification_recipients 
        WHERE notification_id = %s AND recipient_id = %s
        """
        
        cursor.execute(check_query, (notification_id, session['user_id']))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '권한이 없습니다.'}), 403
        
        # 읽음으로 표시
        update_query = """
        UPDATE notification_recipients 
        SET is_read = TRUE, read_at = NOW()
        WHERE notification_id = %s AND recipient_id = %s
        """
        
        cursor.execute(update_query, (notification_id, session['user_id']))
        connection.commit()
        
        success = cursor.rowcount > 0
        cursor.close()
        connection.close()
        
        if success:
            return jsonify({'success': True, 'message': '알림이 읽음으로 표시되었습니다.'})
        else:
            return jsonify({'success': False, 'error': '이미 읽은 알림입니다.'})
        
    except Exception as e:
        logger.error(f"알림 읽음 처리 오류: {e}")
        return jsonify({'success': False, 'error': '알림 처리 중 오류가 발생했습니다.'}), 500

@app.route('/api/student/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """모든 알림을 읽음으로 표시"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        query = """
        UPDATE notification_recipients 
        SET is_read = TRUE, read_at = NOW()
        WHERE recipient_id = %s AND is_read = FALSE
        """
        
        cursor.execute(query, (session['user_id'],))
        connection.commit()
        
        updated_count = cursor.rowcount
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': f'{updated_count}개의 알림이 읽음으로 표시되었습니다.',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"전체 알림 읽음 처리 오류: {e}")
        return jsonify({'success': False, 'error': '알림 처리 중 오류가 발생했습니다.'}), 500

# 관리자 API (기존 admin_api.py에서 가져옴)
@app.route('/api/admin/requirements', methods=['GET'])
@admin_required
def get_graduation_requirements():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        department = request.args.get('department')
        admission_year = request.args.get('admission_year')
        category = request.args.get('category')
        area = request.args.get('area')
        
        query = "SELECT * FROM graduation_requirements WHERE is_active = TRUE"
        params = []
        
        if department:
            query += " AND department = %s"
            params.append(department)
        
        if admission_year:
            query += " AND admission_year = %s"
            params.append(admission_year)

        if category:
            query += " AND category = %s"
            params.append(category)

        if area:
            query += " AND area = %s"
            params.append(area)
        
        query += " ORDER BY department, admission_year, category, area"
        
        cursor.execute(query, params)
        requirements = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'requirements': requirements})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 학과 목록 제공 API (필터/모달 동적 옵션용)
@app.route('/api/admin/departments', methods=['GET'])
@admin_required
def get_departments_list():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL ORDER BY department")
        departments = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'departments': departments})
    except Exception as e:
        logger.error(f"학과 목록 조회 오류: {e}")
        return jsonify({'success': False, 'error': '학과 목록을 불러올 수 없습니다.'}), 500

@app.route('/api/admin/statistics', methods=['GET'])
@admin_required
def get_statistics():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as total FROM students")
        stats['total_students'] = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM students 
            GROUP BY department 
            ORDER BY count DESC
        """)
        stats['students_by_department'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT grade, COUNT(*) as count 
            FROM students 
            GROUP BY grade 
            ORDER BY grade
        """)
        stats['students_by_grade'] = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN overall_completion_rate >= 90 THEN '90% 이상'
                    WHEN overall_completion_rate >= 70 THEN '70-89%'
                    WHEN overall_completion_rate >= 50 THEN '50-69%'
                    ELSE '50% 미만'
                END as completion_range,
                COUNT(*) as count
            FROM graduation_analysis
            GROUP BY completion_range
            ORDER BY completion_range
        """)
        stats['completion_rate_distribution'] = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'statistics': stats})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/requirements', methods=['POST'])
@admin_required
def create_graduation_requirement():
    try:
        data = request.get_json()
        
        required_fields = ['department', 'admission_year', 'category', 'required_credits']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'{field} 필드가 필요합니다.'}), 400
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        query = """
        INSERT INTO graduation_requirements 
        (department, admission_year, category, area, sub_area, required_credits, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            data['department'],
            data['admission_year'],
            data['category'],
            data.get('area'),
            data.get('sub_area'),
            data['required_credits'],
            data.get('description'),
            data.get('is_active', True)
        )
        
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': '졸업요건이 추가되었습니다.'})
        
    except mysql.connector.IntegrityError as e:
        return jsonify({'success': False, 'error': '동일한 졸업요건이 이미 존재합니다.'}), 400
    except Exception as e:
        logger.error(f"졸업요건 추가 오류: {e}")
        return jsonify({'success': False, 'error': '졸업요건 추가 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/requirements/<int:requirement_id>', methods=['PUT'])
@admin_required
def update_graduation_requirement(requirement_id):
    try:
        data = request.get_json()
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 기존 레코드 확인
        cursor.execute("SELECT id FROM graduation_requirements WHERE id = %s", (requirement_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '존재하지 않는 졸업요건입니다.'}), 404
        
        # 업데이트 쿼리
        query = """
        UPDATE graduation_requirements 
        SET department = %s, admission_year = %s, category = %s, area = %s, 
            sub_area = %s, required_credits = %s, description = %s, is_active = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        values = (
            data['department'],
            data['admission_year'],
            data['category'],
            data.get('area'),
            data.get('sub_area'),
            data['required_credits'],
            data.get('description'),
            data.get('is_active', True),
            requirement_id
        )
        
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
        
        # 해당 졸업요건에 영향받는 학생들의 분석 결과 재계산 트리거
        update_affected_students_analysis(data['department'], data['admission_year'])
        
        return jsonify({'success': True, 'message': '졸업요건이 수정되었습니다.'})
        
    except mysql.connector.IntegrityError as e:
        return jsonify({'success': False, 'error': '동일한 졸업요건이 이미 존재합니다.'}), 400
    except Exception as e:
        logger.error(f"졸업요건 수정 오류: {e}")
        return jsonify({'success': False, 'error': '졸업요건 수정 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/requirements/<int:requirement_id>', methods=['DELETE'])
@admin_required
def delete_graduation_requirement(requirement_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 기존 레코드 확인 및 정보 가져오기
        cursor.execute("SELECT department, admission_year FROM graduation_requirements WHERE id = %s", (requirement_id,))
        requirement = cursor.fetchone()
        
        if not requirement:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '존재하지 않는 졸업요건입니다.'}), 404
        
        # 삭제 실행
        cursor.execute("DELETE FROM graduation_requirements WHERE id = %s", (requirement_id,))
        connection.commit()
        cursor.close()
        connection.close()
        
        # 해당 졸업요건에 영향받는 학생들의 분석 결과 재계산 트리거
        update_affected_students_analysis(requirement['department'], requirement['admission_year'])
        
        return jsonify({'success': True, 'message': '졸업요건이 삭제되었습니다.'})
        
    except Exception as e:
        logger.error(f"졸업요건 삭제 오류: {e}")
        return jsonify({'success': False, 'error': '졸업요건 삭제 중 오류가 발생했습니다.'}), 500

def update_affected_students_analysis(department, admission_year):
    """졸업요건 변경 시 영향받는 학생들의 분석 결과를 재계산"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 해당 학과/입학년도 학생들 찾기
        cursor.execute("""
            SELECT DISTINCT s.student_id 
            FROM students s 
            WHERE s.department = %s 
            AND YEAR(s.admission_date) = %s
        """, (department, admission_year))
        
        affected_students = cursor.fetchall()
        cursor.close()
        connection.close()
        
        logger.info(f"졸업요건 변경으로 인한 재분석 대상 학생 수: {len(affected_students)}")
        
        # 각 학생의 분석 결과를 백그라운드에서 재계산
        successful_updates = 0
        for student in affected_students:
            try:
                analyze_student_graduation(student[0], db_config)
                logger.info(f"학생 {student[0]} 분석 결과 업데이트 완료")
                successful_updates += 1
            except Exception as e:
                logger.error(f"학생 {student[0]} 분석 업데이트 실패: {e}")
        
        # 영향받는 학생들에게 알림 전송
        if len(affected_students) > 0:
            notification_title = "졸업요건 변경 안내"
            notification_message = f"""
안녕하세요.

{department} {admission_year}년 입학생 대상 졸업요건이 변경되었습니다.

변경사항:
- 학과: {department}
- 입학년도: {admission_year}년

졸업학점 관리 시스템에 로그인하여 변경된 졸업요건과 새로운 분석 결과를 확인해주세요.
변경된 요건에 따라 이수 계획을 재검토하시기 바랍니다.

감사합니다.
            """.strip()
            
            # 해당 학과/입학년도 학생들에게 그룹 알림 전송
            from notification_system import send_notification_to_students
            
            notification_result = send_notification_to_students(
                sender_id='admin',
                title=notification_title,
                message=notification_message,
                target_type='group',
                target_data={
                    'department': department,
                    'admission_year': admission_year
                },
                is_urgent=True,
                db_config=db_config
            )
            
            if notification_result.get('success'):
                logger.info(f"졸업요건 변경 알림 전송 완료: {notification_result.get('recipients_count', 0)}명")
            else:
                logger.error(f"졸업요건 변경 알림 전송 실패: {notification_result.get('error', '알 수 없는 오류')}")
        
        logger.info(f"졸업요건 변경 처리 완료: {successful_updates}/{len(affected_students)}명 분석 업데이트 성공")
                
    except Exception as e:
        logger.error(f"영향받는 학생 분석 업데이트 오류: {e}")

# 학생 관리 API
@app.route('/api/admin/students', methods=['GET'])
@admin_required
def get_students():
    """학생 목록 조회 및 검색"""
    try:
        logger.info("학생 목록 API 호출됨")
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 파라미터 받기
        search = request.args.get('search', '').strip()
        department = request.args.get('department', '')
        grade = request.args.get('grade', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        logger.info(f"검색 파라미터: search={search}, department={department}, grade={grade}, page={page}")
        
        # 기본 쿼리
        query = """
        SELECT s.student_id, s.name, s.department, s.grade, s.major, s.minor, s.double_major,
               s.admission_date, s.created_at, s.updated_at,
               ga.overall_completion_rate,
               ga.total_completed_credits,
               ga.total_required_credits,
               ga.analysis_date
        FROM students s
        LEFT JOIN graduation_analysis ga ON s.student_id = ga.student_id
        WHERE 1=1
        """
        
        params = []
        
        # 검색 조건 추가
        if search:
            query += " AND (s.student_id LIKE %s OR s.name LIKE %s OR s.department LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if department:
            query += " AND s.department = %s"
            params.append(department)
        
        if grade:
            query += " AND s.grade = %s"
            params.append(int(grade))
        
        # 총 개수 조회
        count_query = """
        SELECT COUNT(DISTINCT s.student_id) as total_count
        FROM students s
        WHERE 1=1
        """
        count_params = []
        
        if search:
            count_query += " AND (s.student_id LIKE %s OR s.name LIKE %s OR s.department LIKE %s)"
            count_params.extend([search_param, search_param, search_param])
        
        if department:
            count_query += " AND s.department = %s"
            count_params.append(department)
        
        if grade:
            count_query += " AND s.grade = %s"
            count_params.append(int(grade))
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total_count']
        
        # 페이징 및 정렬
        query += " ORDER BY s.student_id LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        logger.info(f"실행할 쿼리: {query}")
        logger.info(f"쿼리 파라미터: {params}")
        
        cursor.execute(query, params)
        students = cursor.fetchall()
        
        logger.info(f"조회된 학생 수: {len(students)}")
        
        # Null 값 처리
        for student in students:
            if student['overall_completion_rate'] is None:
                student['overall_completion_rate'] = 0
            if student['total_completed_credits'] is None:
                student['total_completed_credits'] = 0
            if student['total_required_credits'] is None:
                student['total_required_credits'] = 0
        
        # 학과 목록 조회 (필터용)
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL ORDER BY department")
        departments = [row['department'] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        result = {
            'success': True,
            'students': students,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': offset + len(students) < total,
            'departments': departments
        }
        
        logger.info(f"API 응답: success=True, students={len(students)}, total={total}")
        return jsonify(result)
        
    except mysql.connector.Error as db_error:
        logger.error(f"데이터베이스 오류: {db_error}")
        return jsonify({'success': False, 'error': f'데이터베이스 연결 오류: {str(db_error)}'}), 500
    except Exception as e:
        logger.error(f"학생 목록 조회 오류: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'학생 목록을 조회할 수 없습니다: {str(e)}'}), 500

@app.route('/api/admin/students/<student_id>', methods=['GET'])
@admin_required
def get_student_detail(student_id):
    """특정 학생 상세 정보 조회"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 기본 학생 정보
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '학생을 찾을 수 없습니다.'}), 404
        
        # 분석 결과
        cursor.execute("""
            SELECT * FROM graduation_analysis 
            WHERE student_id = %s 
            ORDER BY analysis_date DESC
        """, (student_id,))
        analyses = cursor.fetchall()
        
        # 수강 기록 요약
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as course_count,
                SUM(CASE WHEN grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P') THEN credit ELSE 0 END) as total_credits
            FROM course_records 
            WHERE student_id = %s
            GROUP BY category
            ORDER BY category
        """, (student_id,))
        course_summary = cursor.fetchall()
        
        # 알림 수신 통계
        cursor.execute("""
            SELECT 
                COUNT(*) as total_notifications,
                SUM(CASE WHEN nr.is_read = 0 THEN 1 ELSE 0 END) as unread_count
            FROM notification_recipients nr
            WHERE nr.recipient_id = %s
        """, (student_id,))
        notification_stats = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'student': student,
            'analyses': analyses,
            'course_summary': course_summary,
            'notification_stats': notification_stats
        })
        
    except Exception as e:
        logger.error(f"학생 상세 정보 조회 오류: {e}")
        return jsonify({'success': False, 'error': '학생 정보를 조회할 수 없습니다.'}), 500

@app.route('/api/admin/students/<student_id>', methods=['PUT'])
@admin_required
def update_student(student_id):
    """학생 정보 수정"""
    try:
        data = request.get_json()
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 기존 학생 확인
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '학생을 찾을 수 없습니다.'}), 404
        
        # 수정 가능한 필드 정의
        updatable_fields = [
            'name', 'department', 'major', 'minor', 'double_major',
            'grade', 'university', 'course_type', 'curriculum_year'
        ]
        
        update_parts = []
        params = []
        
        for field in updatable_fields:
            if field in data:
                update_parts.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_parts:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '수정할 데이터가 없습니다.'}), 400
        
        # 업데이트 실행
        query = f"UPDATE students SET {', '.join(update_parts)}, updated_at = CURRENT_TIMESTAMP WHERE student_id = %s"
        params.append(student_id)
        
        cursor.execute(query, params)
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': '학생 정보가 수정되었습니다.'})
        
    except Exception as e:
        logger.error(f"학생 정보 수정 오류: {e}")
        return jsonify({'success': False, 'error': '학생 정보 수정 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/students/<student_id>/reanalyze', methods=['POST'])
@admin_required
def reanalyze_student(student_id):
    """학생 졸업요건 재분석"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 학생 존재 확인
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '학생을 찾을 수 없습니다.'}), 404
        
        cursor.close()
        connection.close()
        
        # 분석 실행
        analysis_result = analyze_student_graduation(student_id, db_config)
        
        if 'error' in analysis_result:
            return jsonify({'success': False, 'error': f"분석 실패: {analysis_result['error']}"}), 500
        
        return jsonify({
            'success': True,
            'message': '졸업요건 분석이 완료되었습니다.',
            'analysis_summary': {
                'completion_rate': analysis_result.get('overall_completion_rate', 0),
                'completed_credits': analysis_result.get('total_completed_credits', 0),
                'required_credits': analysis_result.get('total_required_credits', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"학생 재분석 오류: {e}")
        return jsonify({'success': False, 'error': '분석 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/students/send-notification', methods=['POST'])
@admin_required
def send_student_notification():
    """학생들에게 알림 발송"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'message', 'target_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'{field} 필드가 필요합니다.'}), 400
        
        from notification_system import send_notification_to_students
        
        # 대상에 따른 알림 전송
        if data['target_type'] == 'individual':
            target_data = data.get('student_ids', [])
        elif data['target_type'] == 'group':
            target_data = data.get('filter_criteria', {})
        else:  # 'all'
            target_data = None
        
        result = send_notification_to_students(
            sender_id=session['user_id'],
            title=data['title'],
            message=data['message'],
            target_type=data['target_type'],
            target_data=target_data,
            is_urgent=data.get('is_urgent', False),
            db_config=db_config
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f"알림이 {result.get('recipients_count', 0)}명에게 전송되었습니다.",
                'recipients_count': result.get('recipients_count', 0)
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', '알림 전송에 실패했습니다.')})
        
    except Exception as e:
        logger.error(f"학생 알림 발송 오류: {e}")
        return jsonify({'success': False, 'error': '알림 발송 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/students/bulk-action', methods=['POST'])
@admin_required
def bulk_student_action():
    """학생 일괄 처리"""
    try:
        data = request.get_json()
        
        action = data.get('action')
        student_ids = data.get('student_ids', [])
        
        if not action or not student_ids:
            return jsonify({'success': False, 'error': '작업과 대상 학생을 선택해주세요.'}), 400
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        success_count = 0
        
        if action == 'reanalyze':
            # 일괄 재분석
            for student_id in student_ids:
                try:
                    analysis_result = analyze_student_graduation(student_id, db_config)
                    if 'error' not in analysis_result:
                        success_count += 1
                except Exception as e:
                    logger.warning(f"학생 {student_id} 분석 실패: {e}")
        
        elif action == 'update_grade':
            # 학년 일괄 업데이트
            new_grade = data.get('new_grade')
            if not new_grade:
                return jsonify({'success': False, 'error': '새 학년을 입력해주세요.'}), 400
            
            placeholders = ','.join(['%s'] * len(student_ids))
            query = f"UPDATE students SET grade = %s, updated_at = CURRENT_TIMESTAMP WHERE student_id IN ({placeholders})"
            cursor.execute(query, [new_grade] + student_ids)
            connection.commit()
            success_count = cursor.rowcount
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': f'{success_count}명의 학생에 대해 작업이 완료되었습니다.',
            'success_count': success_count,
            'total_count': len(student_ids)
        })
        
    except Exception as e:
        logger.error(f"일괄 처리 오류: {e}")
        return jsonify({'success': False, 'error': '일괄 처리 중 오류가 발생했습니다.'}), 500

# 관리자 알림 관리 API
@app.route('/admin/notifications')
@admin_required
def admin_notifications():
    """관리자 알림 관리 페이지"""
    return render_template('admin_notifications.html')

# 추천 진단 API (관리자/개발용)
@app.route('/api/debug/recommendation/<student_id>', methods=['GET'])
@login_required
def debug_recommendation(student_id):
    """특정 학생의 추천 생성 경로를 진단합니다."""
    try:
        checker = GraduationRequirementsChecker(db_config)
        checker.connect_db()
        try:
            info = checker.get_student_info(student_id)
            if not info:
                return jsonify({'success': False, 'error': '학생 정보를 찾을 수 없습니다.'}), 404
            admission_year = checker._extract_admission_year(info.get('admission_date'))
            department = info.get('department')
            courses = checker.get_student_courses(student_id)
            requirements = checker.get_graduation_requirements(department, admission_year)
            recognition = checker.get_major_elective_recognition(department, admission_year)
            adjusted = checker._apply_recognition_rules(courses, recognition)
            completed = checker._calculate_completed_credits(adjusted)
            curriculum = checker.get_curriculum_courses(department, admission_year)
            passed_codes = list(checker._collect_passed_course_codes(adjusted))

            # 전필/전선 부족 추출
            missing = []
            for r in requirements:
                cat = r.get('category')
                area = r.get('area')
                req = float(r.get('required_credits') or 0)
                key = f"{cat}_{area}" if area else cat
                comp = float(completed.get(key, 0.0))
                if req > 0 and comp < req:
                    missing.append({
                        'category': cat,
                        'area': area,
                        'required_credits': req,
                        'completed_credits': comp,
                        'missing_credits': req - comp
                    })

            # 추천 풀 구성 및 제외 카운트
            required_pool = [c for c in curriculum if (c.get('required_type') == '전필' and (c.get('course_code') or '').strip() not in passed_codes)]
            elective_pool = [c for c in curriculum if (c.get('required_type') == '전선' and (c.get('course_code') or '').strip() not in passed_codes)]
            required_excluded = [c for c in curriculum if (c.get('required_type') == '전필' and (c.get('course_code') or '').strip() in passed_codes)]
            elective_excluded = [c for c in curriculum if (c.get('required_type') == '전선' and (c.get('course_code') or '').strip() in passed_codes)]

            return jsonify({
                'success': True,
                'student': {
                    'student_id': student_id,
                    'department': department,
                    'admission_year': admission_year
                },
                'curriculum': {
                    'count': len(curriculum)
                },
                'missing_requirements': missing,
                'recommendation_pools': {
                    'required_candidates': len(required_pool),
                    'elective_candidates': len(elective_pool),
                    'required_excluded_as_passed': len(required_excluded),
                    'elective_excluded_as_passed': len(elective_excluded)
                },
                'passed_codes': passed_codes[:50]
            })
        finally:
            checker.disconnect_db()
    except Exception as e:
        logger.error(f"추천 진단 오류: {e}")
        return jsonify({'success': False, 'error': '진단 중 오류가 발생했습니다.'}), 500

@app.route('/api/admin/notifications', methods=['GET'])
@admin_required
def get_admin_notifications():
    """관리자용 알림 목록 조회"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', '').strip()
        offset = (page - 1) * limit
        
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 기본 쿼리
        query = """
        SELECT n.id, n.sender_id, n.title, n.message, n.target_type, 
               n.target_filter, n.is_urgent, n.sent_at,
               COUNT(nr.notification_id) as recipients_count,
               SUM(CASE WHEN nr.is_read = TRUE THEN 1 ELSE 0 END) as read_count
        FROM notifications n
        LEFT JOIN notification_recipients nr ON n.id = nr.notification_id
        WHERE 1=1
        """
        
        params = []
        
        # 검색 조건
        if search:
            query += " AND (n.title LIKE %s OR n.message LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        query += " GROUP BY n.id ORDER BY n.sent_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        notifications = cursor.fetchall()
        
        # 총 개수 조회
        count_query = "SELECT COUNT(*) as total FROM notifications WHERE 1=1"
        count_params = []
        
        if search:
            count_query += " AND (title LIKE %s OR message LIKE %s)"
            count_params.extend([search_param, search_param])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': offset + len(notifications) < total
        })
        
    except Exception as e:
        logger.error(f"관리자 알림 목록 조회 오류: {e}")
        return jsonify({'success': False, 'error': '알림 목록을 조회할 수 없습니다.'}), 500

@app.route('/api/admin/notifications/<int:notification_id>', methods=['GET'])
@admin_required
def get_admin_notification_detail(notification_id):
    """특정 알림 상세 정보 조회"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 알림 기본 정보
        cursor.execute("""
            SELECT n.*, 
                   COUNT(nr.notification_id) as recipients_count,
                   SUM(CASE WHEN nr.is_read = TRUE THEN 1 ELSE 0 END) as read_count
            FROM notifications n
            LEFT JOIN notification_recipients nr ON n.id = nr.notification_id
            WHERE n.id = %s
            GROUP BY n.id
        """, (notification_id,))
        
        notification = cursor.fetchone()
        
        if not notification:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': '알림을 찾을 수 없습니다.'}), 404
        
        # 수신자 목록 (최대 100명까지)
        cursor.execute("""
            SELECT nr.recipient_id, nr.is_read, nr.read_at, s.name
            FROM notification_recipients nr
            LEFT JOIN students s ON nr.recipient_id = s.student_id
            WHERE nr.notification_id = %s
            ORDER BY nr.is_read ASC, nr.recipient_id
            LIMIT 100
        """, (notification_id,))
        
        recipients = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'notification': notification,
            'recipients': recipients
        })
        
    except Exception as e:
        logger.error(f"알림 상세 조회 오류: {e}")
        return jsonify({'success': False, 'error': '알림 상세 정보를 조회할 수 없습니다.'}), 500

@app.route('/api/admin/notifications/<int:notification_id>', methods=['DELETE'])
@admin_required
def delete_admin_notification(notification_id):
    """알림 삭제 (관리자용)"""
    try:
        notification_system = NotificationSystem(db_config)
        notification_system.connect_db()
        
        # 먼저 알림이 존재하는지 확인
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT id, sender_id, title FROM notifications WHERE id = %s", (notification_id,))
        notification = cursor.fetchone()
        
        if not notification:
            cursor.close()
            connection.close()
            notification_system.disconnect_db()
            return jsonify({'success': False, 'error': '존재하지 않는 알림입니다.'}), 404
        
        # 권한 확인 (관리자는 모든 알림 삭제 가능)
        if session.get('role') == 'admin':
            # 관리자는 모든 알림 삭제 가능 - 원래 발송자 ID 사용
            sender_id = notification['sender_id']
        else:
            # 일반 사용자는 자신이 발송한 알림만 삭제 가능
            sender_id = session['user_id']
        
        cursor.close()
        connection.close()
        
        success = notification_system.delete_notification(notification_id, sender_id)
        notification_system.disconnect_db()
        
        if success:
            logger.info(f"관리자 {session['user_id']}가 알림 {notification_id} 삭제: {notification['title']}")
            return jsonify({
                'success': True, 
                'message': f"알림 '{notification['title']}'이(가) 삭제되었습니다."
            })
        else:
            return jsonify({
                'success': False, 
                'error': '알림 삭제 권한이 없거나 삭제에 실패했습니다.'
            }), 403
        
    except Exception as e:
        logger.error(f"관리자 알림 삭제 오류: {e}")
        return jsonify({'success': False, 'error': f'알림 삭제 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/admin/notifications/statistics', methods=['GET'])
@admin_required
def get_notification_statistics():
    """알림 통계 조회"""
    try:
        notification_system = NotificationSystem(db_config)
        notification_system.connect_db()
        
        # 전체 통계
        total_stats = notification_system.get_notification_statistics()
        
        # 발송자별 통계 (관리자용)
        sender_stats = notification_system.get_notification_statistics(session['user_id'])
        
        notification_system.disconnect_db()
        
        return jsonify({
            'success': True,
            'total_statistics': total_stats,
            'sender_statistics': sender_stats
        })
        
    except Exception as e:
        logger.error(f"알림 통계 조회 오류: {e}")
        return jsonify({'success': False, 'error': '통계를 조회할 수 없습니다.'}), 500

def setup_database():
    """데이터베이스 초기 설정 및 필요한 컬럼 추가"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # students 테이블에 필요한 컬럼이 있는지 확인
        cursor.execute("SHOW COLUMNS FROM students LIKE 'phone'")
        phone_exists = cursor.fetchone() is not None
        
        cursor.execute("SHOW COLUMNS FROM students LIKE 'email'")
        email_exists = cursor.fetchone() is not None
        
        # 필요한 컬럼 추가
        if not phone_exists or not email_exists:
            alter_queries = []
            if not phone_exists:
                alter_queries.append("ADD COLUMN phone VARCHAR(20) COMMENT '전화번호' AFTER admission_date")
            if not email_exists:
                alter_queries.append("ADD COLUMN email VARCHAR(100) COMMENT '이메일' AFTER phone")
            
            if alter_queries:
                alter_query = f"ALTER TABLE students {', '.join(alter_queries)}"
                cursor.execute(alter_query)
                connection.commit()
                print("테이블 구조가 업데이트되었습니다.")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"데이터베이스 설정 오류: {e}")

if __name__ == '__main__':
    # 데이터베이스 설정
    setup_database()
    
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