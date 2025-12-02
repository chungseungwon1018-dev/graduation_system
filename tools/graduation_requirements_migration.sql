-- 졸업요건 마이그레이션 SQL
-- 생성일시: 2025-10-27 23:19:51

-- NOTE: 아래 ALTER TABLE은 graduation_requirements에 max_credits 컬럼이 없을 때만 실행하세요
ALTER TABLE graduation_requirements ADD COLUMN IF NOT EXISTS max_credits DECIMAL(4,1) NULL AFTER required_credits;

CREATE TABLE IF NOT EXISTS graduation_requirements_backup_20251027_231951 AS SELECT * FROM graduation_requirements;

START TRANSACTION;


INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '교양', '개신기초교양', '인성과 비판적 사고', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '교양', '개신기초교양', '의사소통', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '교양', '개신기초교양', '영어', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '교양', '개신기초교양', '정보문해', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '교양', '일반교양', '-', 12.0, NULL, '최저이수학점: 12.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '교양', '확대교양', '-', 6.0, NULL, '최저이수학점: 6.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '기타', '총교양학점', NULL, 30.0, 40.0, '최저이수학점: 30.0, 상한학점: 40.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '전공', '전공필수', NULL, 30.0, NULL, '최저이수학점: 30.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '전공', '전공선택', NULL, 15.0, NULL, '최저이수학점: 15.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, '기타', '총학점', NULL, 130.0, NULL, '최저이수학점: 130.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '개신기초교양', '인성과 비판적 사고', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '개신기초교양', '의사소통', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '개신기초교양', '영어', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '개신기초교양', '정보문해', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '일반교양', '-', 12.0, NULL, '최저이수학점: 12.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '확대교양', '-', 6.0, NULL, '최저이수학점: 6.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '교양', '교양총계', NULL, 30.0, 40.0, '최저이수학점: 30.0, 상한학점: 40.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '전공', '전공필수', NULL, 30.0, NULL, '최저이수학점: 30.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '전공', '전공선택', NULL, 15.0, NULL, '최저이수학점: 15.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2022, '총학점', '학점총계', NULL, 130.0, NULL, '최저이수학점: 130.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '개신기초교양', '인성과 비판적 사고', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '개신기초교양', '의사소통', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '개신기초교양', '영어', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '개신기초교양', '정보문해', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '일반교양', '-', 12.0, NULL, '최저이수학점: 12.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '확대교양', '-', 6.0, NULL, '최저이수학점: 6.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '교양', '교양총계', NULL, 30.0, 40.0, '최저이수학점: 30.0, 상한학점: 40.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '전공', '전공필수', NULL, 30.0, NULL, '최저이수학점: 30.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '전공', '전공선택', NULL, 15.0, NULL, '최저이수학점: 15.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2023, '총학점', '학점총계', NULL, 130.0, NULL, '최저이수학점: 130.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '개신기초교양', '인성과 비판적 사고', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '개신기초교양', '의사소통', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '개신기초교양', '영어', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '개신기초교양', '정보문해', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '일반교양', '-', 12.0, NULL, '최저이수학점: 12.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '확대교양', '-', 6.0, NULL, '최저이수학점: 6.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '교양', '교양총계', NULL, 30.0, 40.0, '최저이수학점: 30.0, 상한학점: 40.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '전공', '전공필수', NULL, 30.0, NULL, '최저이수학점: 30.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '전공', '전공선택', NULL, 15.0, NULL, '최저이수학점: 15.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2024, '총학점', '학점총계', NULL, 130.0, NULL, '최저이수학점: 130.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '개신기초교양', '인성과 비판적 사고', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '개신기초교양', '의사소통', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '개신기초교양', '영어', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '개신기초교양', '정보문해', 3.0, NULL, '최저이수학점: 3.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '일반교양', '-', 12.0, NULL, '최저이수학점: 12.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '확대교양', '-', 6.0, NULL, '최저이수학점: 6.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '교양', '교양총계', NULL, 30.0, 40.0, '최저이수학점: 30.0, 상한학점: 40.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '전공', '전공필수', NULL, 30.0, NULL, '최저이수학점: 30.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '전공', '전공선택', NULL, 15.0, NULL, '최저이수학점: 15.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2025, '총학점', '학점총계', NULL, 130.0, NULL, '최저이수학점: 130.0', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', None, '교양', '', NULL, NULL, NULL, '최저이수학점: NULL', TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;

-- 파일 설명(메모) 추가
INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('경영정보학과', 2021, 'meta', '설명', NULL, NULL, NULL, '일반교양은 인간과 문화, 사회와 역사, 자연과 과학 각 분야별 1과목 이상으로 최저 12학점을 이수해야 함.\n확대교양은 6학점 이상 이수해야함. 최저 6학점을 이수해야 함.\n기타 카테고리는 각 졸업요건을 영역별로 묶어 데이터 처리 시의 편의성을 위해 만들어짐\n기타 카테고리의 총교양학점은 교양 카테고리 과목의 합계로 최저이수학점 30 이상 상한학점 40이하의 영역에 속하는지 확인을 위해 사용\n기타 카테고리의 총학점은 학점의 총계로 교양과 전공 학점의 총계를 나타내며 학점 총계 이상으로 학점을 이수하였는지 확인', TRUE)
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    updated_at = CURRENT_TIMESTAMP;
COMMIT;
