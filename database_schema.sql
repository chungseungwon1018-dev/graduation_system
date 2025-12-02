-- 졸업학점 관리 시스템 MySQL 스키마
-- 생성일: 2025-06-02
-- 연결정보: host=203.255.78.58, port=9003, user=user29

CREATE DATABASE IF NOT EXISTS graduation_system 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE graduation_system;

-- 1. 사용자 계정 테이블 (로그인 관리)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '로그인 ID (학번)',
    password_hash VARCHAR(255) NOT NULL COMMENT '암호화된 비밀번호',
    role ENUM('student', 'admin') NOT NULL DEFAULT 'student' COMMENT '사용자 역할',
    is_active BOOLEAN DEFAULT TRUE COMMENT '계정 활성화 상태',
    last_login DATETIME COMMENT '마지막 로그인 시간',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role)
) COMMENT='사용자 계정 정보';

-- 2. 학생 정보 테이블 (개인정보 및 학적 정보)
CREATE TABLE students (
    student_id VARCHAR(20) PRIMARY KEY COMMENT '학번',
    university VARCHAR(100) COMMENT '대학',
    department VARCHAR(100) COMMENT '학과',
    major VARCHAR(100) COMMENT '전공',
    minor VARCHAR(100) COMMENT '부전공',
    double_major VARCHAR(100) COMMENT '다전공',
    course_type VARCHAR(50) COMMENT '과정 (학사/석사/박사)',
    admission_date DATE COMMENT '입학일자',
    phone VARCHAR(20) COMMENT '전화번호',
    email VARCHAR(100) COMMENT '이메일',
    name VARCHAR(50) NOT NULL COMMENT '성명',
    curriculum_year YEAR COMMENT '교과 적용년도',
    semester VARCHAR(20) COMMENT '이수학기',
    birth_date DATE COMMENT '생년월일',
    grade INT COMMENT '학년',
    counseling_count INT DEFAULT 0 COMMENT '평생사제상담 건수',
    major_required_credits FLOAT DEFAULT NULL COMMENT '전공필수학점 (엑셀 고정칸 AC22)',
    major_elective_credits FLOAT DEFAULT NULL COMMENT '전공선택학점 (엑셀 고정칸 AH22)',
    general_elective_credits FLOAT DEFAULT NULL COMMENT '일반선택학점 (엑셀 고정칸 Y22)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(username) ON UPDATE CASCADE,
    INDEX idx_department (department),
    INDEX idx_admission_date (admission_date),
    INDEX idx_grade (grade)
) COMMENT='학생 개인정보 및 학적정보';

-- 3. 수강 기록 테이블 (이수학점 정보)
CREATE TABLE course_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL COMMENT '학번',
    category VARCHAR(50) COMMENT '구분 (교양/전공/기타)',
    area VARCHAR(100) COMMENT '영역',
    sub_area VARCHAR(100) COMMENT '세부영역',
    year YEAR COMMENT '수강년도',
    semester VARCHAR(10) COMMENT '수강학기',
    course_code VARCHAR(20) COMMENT '교과목번호',
    course_name VARCHAR(200) NOT NULL COMMENT '교과목명',
    credit DECIMAL(3,1) COMMENT '학점',
    completion_type VARCHAR(50) COMMENT '이수구분',
    grade VARCHAR(10) COMMENT '성적',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    INDEX idx_student_id (student_id),
    INDEX idx_category (category),
    INDEX idx_year_semester (year, semester),
    INDEX idx_course_code (course_code)
) COMMENT='학생 수강기록';

-- 4. 졸업 요건 테이블 (학과별/연도별 졸업 기준)
CREATE TABLE graduation_requirements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(100) NOT NULL COMMENT '학과',
    admission_year YEAR NOT NULL COMMENT '입학년도',
    category VARCHAR(50) NOT NULL COMMENT '구분 (교양/전공/기타)',
    area VARCHAR(100) COMMENT '영역',
    sub_area VARCHAR(100) COMMENT '세부영역',
    required_credits DECIMAL(4,1) NOT NULL COMMENT '필요학점',
    max_credits DECIMAL(4,1) NULL COMMENT '상한학점(교양 등 상한 적용 시 사용)',
    description TEXT COMMENT '요건 설명',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성화 상태',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_requirement (department, admission_year, category, area, sub_area),
    INDEX idx_dept_year (department, admission_year),
    INDEX idx_category (category)
) COMMENT='졸업요건 기준';

-- 5. 졸업 분석 결과 테이블 (분석 결과 저장)
CREATE TABLE graduation_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL COMMENT '학번',
    analysis_date DATETIME NOT NULL COMMENT '분석 실행 일시',
    total_completed_credits DECIMAL(5,1) COMMENT '총 이수학점',
    total_required_credits DECIMAL(5,1) COMMENT '총 필요학점',
    overall_completion_rate DECIMAL(5,2) COMMENT '전체 이수율 (%)',
    analysis_result JSON COMMENT '상세 분석 결과 (JSON)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_analysis (student_id),
    INDEX idx_analysis_date (analysis_date),
    INDEX idx_completion_rate (overall_completion_rate)
) COMMENT='졸업요건 분석결과';

-- 6. 알림 테이블 (관리자가 학생에게 보내는 메시지)
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id VARCHAR(20) NOT NULL COMMENT '발송자 ID (관리자)',
    title VARCHAR(200) NOT NULL COMMENT '알림 제목',
    message TEXT NOT NULL COMMENT '알림 내용',
    target_type ENUM('individual', 'group', 'all') NOT NULL COMMENT '대상 유형',
    target_filter JSON COMMENT '그룹 대상 필터 조건 (JSON)',
    is_urgent BOOLEAN DEFAULT FALSE COMMENT '긴급 알림 여부',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(username),
    INDEX idx_sent_at (sent_at),
    INDEX idx_target_type (target_type)
) COMMENT='알림 발송 기록';

-- 7. 알림 수신 기록 테이블 (개별 학생의 알림 읽음 상태)
CREATE TABLE notification_recipients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_id INT NOT NULL COMMENT '알림 ID',
    recipient_id VARCHAR(20) NOT NULL COMMENT '수신자 ID (학생)',
    is_read BOOLEAN DEFAULT FALSE COMMENT '읽음 상태',
    read_at DATETIME COMMENT '읽은 시간',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(username),
    UNIQUE KEY unique_notification_recipient (notification_id, recipient_id),
    INDEX idx_recipient_read (recipient_id, is_read),
    INDEX idx_notification_id (notification_id)
) COMMENT='알림 수신 및 읽음 상태';

-- 8. 시스템 로그 테이블 (사용자 활동 추적)
CREATE TABLE system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(20) COMMENT '사용자 ID',
    action VARCHAR(100) NOT NULL COMMENT '수행 작업',
    table_name VARCHAR(50) COMMENT '대상 테이블',
    record_id VARCHAR(50) COMMENT '대상 레코드 ID',
    old_values JSON COMMENT '변경 전 값',
    new_values JSON COMMENT '변경 후 값',
    ip_address VARCHAR(45) COMMENT '접속 IP',
    user_agent TEXT COMMENT '사용자 에이전트',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(username),
    INDEX idx_user_action (user_id, action),
    INDEX idx_created_at (created_at),
    INDEX idx_table_record (table_name, record_id)
) COMMENT='시스템 활동 로그';

-- 9. 추천 교과목 테이블 (부족 영역별 추천 과목)
CREATE TABLE recommended_courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department VARCHAR(100) NOT NULL COMMENT '학과',
    category VARCHAR(50) NOT NULL COMMENT '구분',
    area VARCHAR(100) COMMENT '영역',
    course_code VARCHAR(20) COMMENT '교과목번호',
    course_name VARCHAR(200) NOT NULL COMMENT '교과목명',
    credit DECIMAL(3,1) COMMENT '학점',
    description TEXT COMMENT '과목 설명',
    prerequisite VARCHAR(500) COMMENT '선수과목',
    semester_offered VARCHAR(20) COMMENT '개설학기 (1학기/2학기/연중)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성화 상태',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_category (department, category),
    INDEX idx_course_code (course_code),
    INDEX idx_area (area)
) COMMENT='추천 교과목 정보';

-- 9a. 커리큘럼 교과목 테이블 (입학년도 범위별 전필/전선 기준)
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
    -- 동일 학과/입학범위/과목/전필여부 조합은 1건으로 유지
    UNIQUE KEY uniq_curriculum_course (department, admission_year_from, admission_year_to, course_code, required_type),
    INDEX idx_dept_range (department, admission_year_from, admission_year_to),
    INDEX idx_course_code (course_code),
    INDEX idx_required_type (required_type)
) COMMENT='학과 커리큘럼 교과목 기준(입학년도 범위별)';

-- 9b. 교과목 대체/동등처리 그룹 (코드 변경/대체과목 관리)
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

-- 9c. 타학과 전공선택 인정 규칙 테이블
-- 사용 예:
-- - 규칙형: source_college='경영대학', required_type_source='전필'이면 경영정보학과에서 '전선'으로 인정
-- - 개별과목형: 특정 타학과/코드 과목을 경영정보학과 전선으로 인정
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

-- 10. 세션 관리 테이블 (웹 세션 관리)
CREATE TABLE user_sessions (
    id VARCHAR(128) PRIMARY KEY COMMENT '세션 ID',
    user_id VARCHAR(20) NOT NULL COMMENT '사용자 ID',
    ip_address VARCHAR(45) COMMENT '접속 IP',
    user_agent TEXT COMMENT '사용자 에이전트',
    last_activity DATETIME NOT NULL COMMENT '마지막 활동 시간',
    expires_at DATETIME NOT NULL COMMENT '세션 만료 시간',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(username) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_last_activity (last_activity)
) COMMENT='사용자 세션 관리';

-- 초기 데이터 삽입

-- 관리자 계정 생성 (비밀번호: admin123 - 실제 운영에서는 강력한 비밀번호 사용)
INSERT INTO users (username, password_hash, role) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/4GhJYwNY6.LUKbqTK', 'admin');

-- 샘플 졸업요건 데이터 (컴퓨터공학과 2023년 입학생 기준)
INSERT INTO graduation_requirements (department, admission_year, category, area, required_credits, description) VALUES
('컴퓨터공학과', 2023, '교양', '기초교양', 15.0, '기초교양 필수'),
('컴퓨터공학과', 2023, '교양', '핵심교양', 18.0, '핵심교양 6개 영역에서 각 3학점'),
('컴퓨터공학과', 2023, '교양', '일반교양', 9.0, '일반교양 자유선택'),
('컴퓨터공학과', 2023, '전공', '전공필수', 45.0, '전공필수 과목'),
('컴퓨터공학과', 2023, '전공', '전공선택', 21.0, '전공선택 과목'),
('컴퓨터공학과', 2023, '기타', '자유선택', 20.0, '자유선택 과목'),
('컴퓨터공학과', 2023, '기타', '졸업논문', 0.0, '졸업논문 또는 종합설계'),
('컴퓨터공학과', 2023, '기타', '상담', 0.0, '평생사제상담 8회 이상');

-- 샘플 추천 교과목 데이터
INSERT INTO recommended_courses (department, category, area, course_code, course_name, credit, semester_offered) VALUES
('컴퓨터공학과', '교양', '기초교양', 'GE001', '대학수학1', 3.0, '1학기'),
('컴퓨터공학과', '교양', '기초교양', 'GE002', '대학물리1', 3.0, '1학기'),
('컴퓨터공학과', '전공', '전공필수', 'CS101', '프로그래밍기초', 3.0, '1학기'),
('컴퓨터공학과', '전공', '전공필수', 'CS201', '자료구조', 3.0, '2학기'),
('컴퓨터공학과', '전공', '전공선택', 'CS301', '데이터베이스', 3.0, '1학기'),
('컴퓨터공학과', '전공', '전공선택', 'CS302', '소프트웨어공학', 3.0, '2학기');

-- 인덱스 최적화를 위한 추가 인덱스
CREATE INDEX idx_course_records_composite ON course_records(student_id, category, area);
CREATE INDEX idx_graduation_analysis_composite ON graduation_analysis(student_id, analysis_date);
CREATE INDEX idx_notifications_composite ON notifications(target_type, sent_at);

-- 뷰 생성: 학생별 이수 현황 요약
CREATE VIEW student_credit_summary AS
SELECT 
    s.student_id,
    s.name,
    s.department,
    s.grade,
    COUNT(cr.id) as total_courses,
    SUM(CASE WHEN cr.grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P') THEN cr.credit ELSE 0 END) as total_credits,
    SUM(CASE WHEN cr.category = '교양' AND cr.grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P') THEN cr.credit ELSE 0 END) as liberal_arts_credits,
    SUM(CASE WHEN cr.category = '전공' AND cr.grade IN ('A+','A0','A-','B+','B0','B-','C+','C0','C-','D+','D0','P') THEN cr.credit ELSE 0 END) as major_credits,
    s.updated_at as last_updated
FROM students s
LEFT JOIN course_records cr ON s.student_id = cr.student_id
GROUP BY s.student_id, s.name, s.department, s.grade, s.updated_at;

-- 뷰 생성: 미읽은 알림 개수
CREATE VIEW unread_notifications_count AS
SELECT 
    nr.recipient_id,
    COUNT(*) as unread_count
FROM notification_recipients nr
WHERE nr.is_read = FALSE
GROUP BY nr.recipient_id;

COMMIT;