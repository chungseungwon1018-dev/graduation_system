from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
from mysql.connector import Error
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from functools import wraps
import os
from enhanced_xlsx_parser import process_excel_file_enhanced as process_excel_file
from graduation_requirements_checker import analyze_student_graduation
from notification_system import get_user_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# 업로드 설정
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 업로드 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class StudentAPI:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
    
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

student_api = StudentAPI({
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
})

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    return render_template('student_dashboard.html', user={'user_id': session['user_id']})

@app.route('/api/student/info', methods=['GET'])
@login_required
def get_student_info():
    try:
        student_api.connect_db()
        cursor = student_api.connection.cursor(dictionary=True)
        
        query = "SELECT * FROM students WHERE student_id = %s"
        cursor.execute(query, (session['user_id'],))
        student = cursor.fetchone()
        cursor.close()
        
        if student:
            return jsonify({
                'success': True,
                'student': student
            })
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
        logger.error(f"학생 정보 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        student_api.disconnect_db()

@app.route('/api/student/analysis', methods=['GET'])
@login_required
def get_student_analysis():
    try:
        student_api.connect_db()
        cursor = student_api.connection.cursor(dictionary=True)
        
        query = """
        SELECT * FROM graduation_analysis 
        WHERE student_id = %s 
        ORDER BY analysis_date DESC 
        LIMIT 1
        """
        cursor.execute(query, (session['user_id'],))
        analysis = cursor.fetchone()
        cursor.close()
        
        if analysis and analysis['analysis_result']:
            analysis_data = json.loads(analysis['analysis_result'])
            return jsonify({
                'success': True,
                'analysis': analysis_data
            })
        else:
            return jsonify({
                'success': True,
                'analysis': None
            })
        
    except Exception as e:
        logger.error(f"분석 결과 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        student_api.disconnect_db()

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
        
        # 파일 크기 체크
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': '파일 크기는 10MB 이하여야 합니다.'}), 400
        
        # 파일 저장
        filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Excel 파일 처리 (향상된 파서 사용)
        try:
            success = process_excel_file(filepath, session['user_id'], student_api.db_config)
            
            if not success:
                # 안전한 파일 정리 (실패 시)
                def cleanup_file(file_path):
                    import time
                    import gc
                    try:
                        gc.collect()
                        time.sleep(0.1)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass  # 실패해도 무시
                
                cleanup_file(filepath)
                
                return jsonify({
                    'error': 'Excel 파일에서 필요한 데이터를 찾을 수 없습니다. 개인정보(학번, 성명)와 수강기록이 포함된 올바른 성적증명서 파일인지 확인해주세요.'
                }), 500
                
        except Exception as excel_error:
            logger.error(f"Excel 파일 처리 중 예외 발생: {excel_error}")
            
            # 안전한 파일 정리 (예외 발생 시)
            def cleanup_file(file_path):
                import time
                import gc
                try:
                    gc.collect()
                    time.sleep(0.1)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass  # 실패해도 무시
            
            cleanup_file(filepath)
            
            # 구체적인 오류 메시지 제공
            error_str = str(excel_error).lower()
            if "required field" in error_str or "필수" in error_str:
                return jsonify({'error': '필수 개인정보(학번, 성명)가 누락되었습니다. 올바른 성적증명서 파일을 업로드해주세요.'}), 500
            elif "cellstyle" in error_str or "applynumberform" in error_str:
                return jsonify({'error': 'Excel 파일에 호환되지 않는 형식이 포함되어 있습니다. 파일을 다른 형식으로 저장 후 다시 시도해주세요.'}), 500
            elif "sheet" in error_str or "시트" in error_str:
                return jsonify({'error': 'Excel 파일의 시트 구조를 읽을 수 없습니다. 파일이 손상되지 않았는지 확인해주세요.'}), 500
            else:
                return jsonify({'error': f'Excel 파일 처리 중 오류가 발생했습니다. 파일 형식을 확인해주세요. (상세 오류: {str(excel_error)[:100]}...)'}), 500
        
        # 졸업요건 분석 실행
        analysis_result = analyze_student_graduation(session['user_id'], student_api.db_config)
        
        if 'error' in analysis_result:
            logger.warning(f"분석 실행 중 경고: {analysis_result['error']}")
        
        # 안전한 파일 정리
        def safe_remove_file(file_path, max_retries=3):
            import time
            import gc
            
            for attempt in range(max_retries):
                try:
                    # 가비지 컬렉션 강제 실행
                    gc.collect()
                    time.sleep(0.2 * (attempt + 1))  # 점진적으로 대기 시간 증가
                    
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"파일 삭제 성공: {file_path}")
                        return True
                except PermissionError as pe:
                    if attempt == max_retries - 1:
                        logger.warning(f"⚠️ 파일 삭제 최종 실패 (사용 중): {file_path} - {pe}")
                        # 나중에 정리하도록 임시 파일명으로 변경
                        try:
                            temp_name = f"{file_path}.temp_delete_{int(time.time())}"
                            os.rename(file_path, temp_name)
                            logger.info(f"파일을 임시 삭제 대기 상태로 변경: {temp_name}")
                        except:
                            pass
                    else:
                        logger.debug(f"파일 삭제 재시도 {attempt + 1}/{max_retries}: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ 파일 삭제 중 오류: {e}")
                    break
            return False
        
        safe_remove_file(filepath)
        
        logger.info(f"파일 업로드 및 분석 완료: 사용자 {session['user_id']}")
        
        return jsonify({
            'success': True,
            'message': '파일 업로드 및 분석이 완료되었습니다.',
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"파일 업로드 오류: {e}")
        return jsonify({'error': '파일 업로드 중 오류가 발생했습니다.'}), 500

@app.route('/api/student/courses', methods=['GET'])
@login_required
def get_student_courses():
    try:
        student_api.connect_db()
        cursor = student_api.connection.cursor(dictionary=True)
        
        query = """
        SELECT * FROM course_records 
        WHERE student_id = %s 
        ORDER BY year DESC, semester DESC, course_name
        """
        cursor.execute(query, (session['user_id'],))
        courses = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'success': True,
            'courses': courses
        })
        
    except Exception as e:
        logger.error(f"수강 기록 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        student_api.disconnect_db()

@app.route('/api/student/notifications', methods=['GET'])
@login_required
def get_student_notifications():
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = get_user_notifications(
            session['user_id'], 
            unread_only=unread_only, 
            db_config=student_api.db_config
        )
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        logger.error(f"알림 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    try:
        from notification_system import NotificationSystem
        
        notification_system = NotificationSystem(student_api.db_config)
        notification_system.connect_db()
        
        success = notification_system.mark_notification_as_read(notification_id, session['user_id'])
        notification_system.disconnect_db()
        
        if success:
            return jsonify({
                'success': True,
                'message': '알림을 읽음으로 표시했습니다.'
            })
        else:
            return jsonify({'error': '알림 상태 변경에 실패했습니다.'}), 400
        
    except Exception as e:
        logger.error(f"알림 읽음 처리 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/student/profile')
@student_required
def student_profile():
    return render_template('student_profile.html', user={'user_id': session['user_id']})

@app.route('/student/notifications')
@student_required
def student_notifications():
    return render_template('student_notifications.html', user={'user_id': session['user_id']})

@app.route('/api/student/dashboard-data')
@login_required
def get_dashboard_data():
    """대시보드에 필요한 모든 데이터를 한 번에 조회"""
    try:
        student_api.connect_db()
        cursor = student_api.connection.cursor(dictionary=True)
        
        # 학생 정보
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (session['user_id'],))
        student = cursor.fetchone()
        
        # 최신 분석 결과
        cursor.execute("""
            SELECT * FROM graduation_analysis 
            WHERE student_id = %s 
            ORDER BY analysis_date DESC 
            LIMIT 1
        """, (session['user_id'],))
        analysis_row = cursor.fetchone()
        
        # 수강 기록 개수
        cursor.execute("""
            SELECT COUNT(*) as total_courses,
                   SUM(CASE WHEN grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P') THEN credit ELSE 0 END) as total_credits
            FROM course_records 
            WHERE student_id = %s
        """, (session['user_id'],))
        course_stats = cursor.fetchone()
        
        # 읽지 않은 알림 개수
        cursor.execute("""
            SELECT COUNT(*) as unread_count
            FROM notification_recipients nr
            WHERE nr.recipient_id = %s AND nr.is_read = FALSE
        """, (session['user_id'],))
        unread_notifications = cursor.fetchone()
        
        cursor.close()
        
        # 분석 결과 파싱
        analysis_data = None
        if analysis_row and analysis_row['analysis_result']:
            analysis_data = json.loads(analysis_row['analysis_result'])
        
        return jsonify({
            'success': True,
            'data': {
                'student': student,
                'analysis': analysis_data,
                'course_stats': course_stats,
                'unread_notifications': unread_notifications['unread_count'] if unread_notifications else 0
            }
        })
        
    except Exception as e:
        logger.error(f"대시보드 데이터 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        student_api.disconnect_db()

@app.route('/api/student/reanalyze', methods=['POST'])
@login_required
def reanalyze_student():
    """기존 데이터로 재분석 실행"""
    try:
        analysis_result = analyze_student_graduation(session['user_id'], student_api.db_config)
        
        if 'error' in analysis_result:
            return jsonify({'error': analysis_result['error']}), 400
        
        return jsonify({
            'success': True,
            'message': '재분석이 완료되었습니다.',
            'analysis': analysis_result
        })
        
    except Exception as e:
        logger.error(f"재분석 오류: {e}")
        return jsonify({'error': '재분석 중 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)