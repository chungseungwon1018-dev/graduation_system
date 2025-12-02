from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
from mysql.connector import Error
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime
from werkzeug.security import check_password_hash
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

class AdminAPI:
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

admin_api = AdminAPI({
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
})

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/requirements', methods=['GET'])
@admin_required
def get_graduation_requirements():
    try:
        admin_api.connect_db()
        cursor = admin_api.connection.cursor(dictionary=True)
        
        department = request.args.get('department')
        admission_year = request.args.get('admission_year')
        
        query = "SELECT * FROM graduation_requirements WHERE is_active = TRUE"
        params = []
        
        if department:
            query += " AND department = %s"
            params.append(department)
        
        if admission_year:
            query += " AND admission_year = %s"
            params.append(admission_year)
        
        query += " ORDER BY department, admission_year, category, area"
        
        cursor.execute(query, params)
        requirements = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'success': True,
            'requirements': requirements
        })
        
    except Exception as e:
        logger.error(f"졸업요건 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/api/admin/requirements', methods=['POST'])
@admin_required
def create_graduation_requirement():
    try:
        data = request.json
        
        required_fields = ['department', 'admission_year', 'category', 'required_credits']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
        
        admin_api.connect_db()
        cursor = admin_api.connection.cursor()
        
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
        admin_api.connection.commit()
        requirement_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'success': True,
            'requirement_id': requirement_id,
            'message': '졸업요건이 생성되었습니다.'
        })
        
    except Error as e:
        admin_api.connection.rollback()
        logger.error(f"졸업요건 생성 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/api/admin/requirements/<int:requirement_id>', methods=['PUT'])
@admin_required
def update_graduation_requirement(requirement_id):
    try:
        data = request.json
        
        admin_api.connect_db()
        cursor = admin_api.connection.cursor()
        
        set_clauses = []
        values = []
        
        updateable_fields = ['department', 'admission_year', 'category', 'area', 
                           'sub_area', 'required_credits', 'description', 'is_active']
        
        for field in updateable_fields:
            if field in data:
                set_clauses.append(f"{field} = %s")
                values.append(data[field])
        
        if not set_clauses:
            return jsonify({'error': '업데이트할 필드가 없습니다.'}), 400
        
        query = f"UPDATE graduation_requirements SET {', '.join(set_clauses)} WHERE id = %s"
        values.append(requirement_id)
        
        cursor.execute(query, values)
        admin_api.connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '해당 졸업요건을 찾을 수 없습니다.'}), 404
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': '졸업요건이 업데이트되었습니다.'
        })
        
    except Error as e:
        admin_api.connection.rollback()
        logger.error(f"졸업요건 업데이트 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/api/admin/requirements/<int:requirement_id>', methods=['DELETE'])
@admin_required
def delete_graduation_requirement(requirement_id):
    try:
        admin_api.connect_db()
        cursor = admin_api.connection.cursor()
        
        cursor.execute("UPDATE graduation_requirements SET is_active = FALSE WHERE id = %s", 
                      (requirement_id,))
        admin_api.connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': '해당 졸업요건을 찾을 수 없습니다.'}), 404
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': '졸업요건이 비활성화되었습니다.'
        })
        
    except Error as e:
        admin_api.connection.rollback()
        logger.error(f"졸업요건 삭제 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/api/admin/students', methods=['GET'])
@admin_required
def get_students():
    try:
        admin_api.connect_db()
        cursor = admin_api.connection.cursor(dictionary=True)
        
        department = request.args.get('department')
        grade = request.args.get('grade')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        conditions = []
        params = []
        
        base_query = """
        SELECT s.*, 
               ga.overall_completion_rate,
               ga.total_completed_credits,
               ga.total_required_credits,
               ga.analysis_date
        FROM students s
        LEFT JOIN graduation_analysis ga ON s.student_id = ga.student_id
        WHERE 1=1
        """
        
        if department:
            conditions.append("s.department = %s")
            params.append(department)
        
        if grade:
            conditions.append("s.grade = %s")
            params.append(grade)
        
        if search:
            conditions.append("(s.name LIKE %s OR s.student_id LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as filtered"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        data_query = base_query + f" ORDER BY s.student_id LIMIT {per_page} OFFSET {(page-1)*per_page}"
        cursor.execute(data_query, params)
        students = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'students': students,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"학생 목록 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/api/admin/students/<student_id>/analysis', methods=['GET'])
@admin_required
def get_student_analysis(student_id):
    try:
        admin_api.connect_db()
        cursor = admin_api.connection.cursor(dictionary=True)
        
        query = "SELECT * FROM graduation_analysis WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        analysis = cursor.fetchone()
        
        if not analysis:
            return jsonify({'error': '해당 학생의 분석 결과를 찾을 수 없습니다.'}), 404
        
        if analysis['analysis_result']:
            analysis['analysis_result'] = json.loads(analysis['analysis_result'])
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"학생 분석 결과 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/api/admin/statistics', methods=['GET'])
@admin_required
def get_statistics():
    try:
        admin_api.connect_db()
        cursor = admin_api.connection.cursor(dictionary=True)
        
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
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        admin_api.disconnect_db()

@app.route('/admin')
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

@app.route('/admin/notifications')
@admin_required
def admin_notifications():
    return render_template('admin_notifications.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)