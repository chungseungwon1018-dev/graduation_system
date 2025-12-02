import mysql.connector
from mysql.connector import Error

# DB 설정 (update_db.py와 동일)
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

DDL_CURRICULUM = """
CREATE TABLE IF NOT EXISTS curriculum_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(100) NOT NULL COMMENT '학과',
    admission_year_from YEAR NOT NULL COMMENT '입학년도 시작(포함)',
    admission_year_to YEAR NOT NULL COMMENT '입학년도 종료(포함, 9999=이후)',
    grade_year TINYINT NULL COMMENT '권장 학년 (선택)',
    term TINYINT NULL COMMENT '권장 학기 (1/2, 선택)',
    required_type ENUM('전필','전선') NOT NULL COMMENT '전공필수/전공선택',
    course_code VARCHAR(20) NOT NULL COMMENT '교과목번호',
    course_name VARCHAR(200) NOT NULL COMMENT '교과목명',
    credits DECIMAL(3,1) NOT NULL COMMENT '학점',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성화 여부',
    metadata JSON NULL COMMENT '부가정보(개설학기, 비고 등)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_curriculum_course (department, admission_year_from, admission_year_to, course_code, required_type),
    INDEX idx_dept_range (department, admission_year_from, admission_year_to),
    INDEX idx_course_code (course_code),
    INDEX idx_required_type (required_type)
) COMMENT='학과 커리큘럼 교과목 기준(입학년도 범위별)';
"""

DDL_EQUIV = """
CREATE TABLE IF NOT EXISTS course_equivalencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(100) NOT NULL COMMENT '학과',
    equivalence_group VARCHAR(50) NOT NULL COMMENT '동등과목 그룹 ID',
    course_code VARCHAR(20) NOT NULL COMMENT '교과목번호',
    course_name VARCHAR(200) NULL COMMENT '교과목명(선택)',
    effective_from YEAR NULL COMMENT '적용 시작년도(선택)',
    effective_to YEAR NULL COMMENT '적용 종료년도(선택)',
    notes VARCHAR(500) NULL COMMENT '비고',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_equiv (department, equivalence_group, course_code),
    INDEX idx_equiv_group (department, equivalence_group)
) COMMENT='교과목 코드 변경/대체과목 동등처리 정의';
"""

DDL_RECOG = """
CREATE TABLE IF NOT EXISTS major_elective_recognition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(100) NOT NULL COMMENT '인정 대상 학과(예: 경영정보학과)',
    admission_year_from YEAR NOT NULL COMMENT '입학년도 시작(포함)',
    admission_year_to YEAR NOT NULL COMMENT '입학년도 종료(포함, 9999=이후)',
    rule_type ENUM('규칙','개별과목') NOT NULL COMMENT '규칙형 또는 개별과목형',
    source_college VARCHAR(100) NULL COMMENT '소속 단과대학(규칙형)',
    source_department VARCHAR(100) NULL COMMENT '소속 학과(개별과목 또는 제한)',
    required_type_source ENUM('전필','전선','기타') NULL COMMENT '원 과목의 이수구분',
    course_code VARCHAR(20) NULL COMMENT '개별과목 코드(개별과목형)',
    course_name VARCHAR(200) NULL COMMENT '개별과목 명(선택)',
    recognized_type ENUM('전선') NOT NULL DEFAULT '전선' COMMENT '인정 구분(현재 전선만 사용)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 여부',
    notes VARCHAR(500) NULL COMMENT '비고',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_range (department, admission_year_from, admission_year_to),
    INDEX idx_rule_type (rule_type),
    INDEX idx_course (course_code),
    INDEX idx_source (source_college, source_department)
) COMMENT='타학과/단과대 과목을 전공선택으로 인정하는 규칙';
"""


def main():
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute(DDL_CURRICULUM)
        cur.execute(DDL_EQUIV)
        cur.execute(DDL_RECOG)
        conn.commit()
        print("스키마 적용 완료: curriculum_courses, course_equivalencies, major_elective_recognition")
    except Error as e:
        print(f"스키마 적용 중 오류: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
