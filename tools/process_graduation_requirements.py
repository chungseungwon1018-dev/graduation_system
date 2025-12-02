import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import sys
from datetime import datetime

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}


def normalize_columns(df):
    """입력 엑셀의 한/영 컬럼명을 표준 키로 매핑"""
    mapping = {
        '입학연도': 'admission_year',
        '학과': 'department',
        '카테고리': 'category',
        '영역': 'area',
        '세부영역': 'sub_area',
        '최저이수학점': 'min_credits',
        '상한학점': 'max_credits',
        # 영어명 가능성
        'admission_year': 'admission_year',
        'department': 'department',
        'category': 'category',
        'area': 'area',
        'sub_area': 'sub_area',
        'min_credits': 'min_credits',
        'max_credits': 'max_credits'
    }

    new_cols = {}
    for col in df.columns:
        key = col.strip() if isinstance(col, str) else col
        if key in mapping:
            new_cols[col] = mapping[key]
        else:
            # 소문자, 공백 제거 형태로 시도
            k2 = str(key).strip().lower().replace(' ', '')
            for cand, std in mapping.items():
                if str(cand).strip().lower().replace(' ', '') == k2:
                    new_cols[col] = std
                    break
    df = df.rename(columns=new_cols)
    return df


def read_requirements_xlsx(file_path):
    """XLSX 파일에서 졸업요건 데이터 읽기 및 A53-A58 설명 추출"""
    try:
        print(f"파일 읽기 시작: {file_path}")
        df = pd.read_excel(file_path, header=0)
        df = normalize_columns(df)
        print(f"데이터 읽기 완료. 총 {len(df)} 행")

        # 시트 하단(예: A53:A58)에 있는 설명문 가져오기 (존재하면)
        # pandas로 전체 시트를 읽었으므로 iloc로 접근
        notes = []
        try:
            # A53은 0-based index 52
            for r in range(52, 58):
                if r < len(df.index):
                    val = df.iloc[r, 0]
                    if pd.notna(val):
                        notes.append(str(val).strip())
        except Exception:
            pass

        # 만약 notes 비어있으면, 빈 리스트 반환
        return df, notes
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        return None, []


def generate_sql(df, notes, output_path):
    """데이터프레임을 SQL INSERT/UPDATE 문으로 변환 (max_credits 추가)"""
    now_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
    sql_statements = []

    sql_statements.append(f"-- 졸업요건 마이그레이션 SQL\n-- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 테이블에 max_credits 컬럼이 없을 경우를 대비한 ALTER문 추가 (idempotent하게 검사하는 쿼리 사용 불가하므로 주석으로 안내)
    sql_statements.append("-- NOTE: 아래 ALTER TABLE은 graduation_requirements에 max_credits 컬럼이 없을 때만 실행하세요")
    sql_statements.append("ALTER TABLE graduation_requirements ADD COLUMN IF NOT EXISTS max_credits DECIMAL(4,1) NULL AFTER required_credits;\n")

    # 백업 생성
    sql_statements.append(f"CREATE TABLE IF NOT EXISTS graduation_requirements_backup_{now_tag} AS SELECT * FROM graduation_requirements;\n")
    sql_statements.append("START TRANSACTION;\n")

    # 데이터 행 필터링: 필수 칼럼이 없거나 값이 비어있으면 건너뜀
    required_cols = ['admission_year', 'department', 'category', 'area', 'min_credits']
    # 빠른 존재 확인
    if any([col not in df.columns for col in required_cols]):
        print("경고: 필수 컬럼 일부가 없습니다. 필요한 컬럼:", ", ".join(required_cols))

    for idx, row in df.iterrows():
        # 최소 필드 유효성: admission_year, department, area, min_credits는 필수
        try:
            if not pd.notna(row.get('admission_year')):
                continue
            if not pd.notna(row.get('department')):
                continue
            if not pd.notna(row.get('area')):
                continue
            if not pd.notna(row.get('min_credits')):
                # 일부 항목은 min_credits가 빈 경우도 있을 수 있으므로 스킵
                continue

            # admission_year 숫자화
            ay = int(row['admission_year'])
            department = str(row['department']).replace("'", "''")
            category = str(row['category']).replace("'", "''") if pd.notna(row.get('category')) else '교양'
            area = str(row['area']).replace("'", "''")
            sub_area = f"'{str(row['sub_area']).replace("'", "''")}'" if 'sub_area' in df.columns and pd.notna(row.get('sub_area')) else 'NULL'
            min_credits = float(row['min_credits'])
            max_credits = float(row['max_credits']) if 'max_credits' in df.columns and pd.notna(row.get('max_credits')) else 'NULL'

            description = f"'최저이수학점: {min_credits}'"
            if max_credits != 'NULL':
                description = f"'최저이수학점: {min_credits}, 상한학점: {max_credits}'"

            sql = f"""
INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('{department}', {ay}, '{category}', '{area}', {sub_area}, {min_credits}, {max_credits}, {description}, TRUE)
ON DUPLICATE KEY UPDATE
    required_credits = VALUES(required_credits),
    max_credits = VALUES(max_credits),
    description = VALUES(description),
    is_active = VALUES(is_active),
    updated_at = CURRENT_TIMESTAMP;"""
            sql_statements.append(sql)
        except Exception:
            # 해당 행 처리 실패 시 건너뜀
            continue

    # 파일 하단 노트(설명)을 별도 레코드로 추가 (department/admission_year 공통값으로 메타 레코드)
    if notes:
        notes_text = '\\n'.join([n.replace("'", "''") for n in notes])
        # 대표 department/admission_year 선택: 첫 데이터 행에서 추출 가능
        try:
            first = df.iloc[0]
            ay0 = int(first['admission_year']) if pd.notna(first['admission_year']) else 2021
            dept0 = str(first['department']).replace("'", "''") if pd.notna(first['department']) else '경영정보학과'
        except Exception:
            ay0 = 2021
            dept0 = '경영정보학과'

        meta_sql = f"""
-- 파일 설명(메모) 추가
INSERT INTO graduation_requirements
    (department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active)
VALUES
    ('{dept0}', {ay0}, 'meta', '설명', NULL, NULL, NULL, '{notes_text}', TRUE)
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    updated_at = CURRENT_TIMESTAMP;"""
        sql_statements.append(meta_sql)

    sql_statements.append("COMMIT;\n")

    # SQL 파일로 저장
    sql_content = '\n'.join(sql_statements)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sql_content)

    print(f"SQL 파일 생성 완료: {output_path}")
    return sql_content


def check_current_requirements(connection):
    """현재 DB의 졸업요건 데이터 조회"""
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT department, admission_year, category, area, sub_area,
               required_credits, max_credits, description, is_active, updated_at
        FROM graduation_requirements
        ORDER BY department, admission_year, category, area;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        print("\n현재 DB 졸업요건 데이터:")
        print("-" * 80)
        for row in results:
            print(f"{row['department']} ({row['admission_year']}) - {row['category']}/{row['area']}: {row['required_credits']} (max: {row.get('max_credits')})")
        print("-" * 80)

        return results
    except Error as e:
        print(f"DB 조회 오류: {e}")
        return None


def main():
    # XLSX 파일 경로
    xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "연도별 졸업요건 정리.xlsx")

    # 결과 SQL 파일 경로
    sql_path = os.path.join(os.path.dirname(__file__), "graduation_requirements_migration.sql")

    print(f"처리 시작...")
    print(f"XLSX 파일: {xlsx_path}")
    print(f"SQL 출력: {sql_path}")

    # XLSX 읽기
    df, notes = read_requirements_xlsx(xlsx_path)
    if df is None:
        print("XLSX 파일 처리 실패")
        return

    # 데이터 미리보기
    print("\n데이터 미리보기:")
    print(df.head())
    print(f"\n총 {len(df)} 개 졸업요건 레코드 확인")

    # 현재 DB 데이터 확인
    try:
        connection = mysql.connector.connect(**db_config)
        current_data = check_current_requirements(connection)
        connection.close()
    except Error as e:
        print(f"DB 연결 오류: {e}")
        current_data = None

    # SQL 생성
    sql_content = generate_sql(df, notes, sql_path)

    print(f"""
처리 완료!
1. 입력 데이터: {len(df)} 행
2. SQL 파일 생성됨: {sql_path}
3. 다음 단계:
   - 생성된 SQL 파일의 내용을 검토해 주세요
   - ALTER TABLE 문은 수동 확인 후 실행 권장 (IF NOT EXISTS 일부 DB엔서포트 다름)
   - 실행 전 백업(자동 생성)과 트랜잭션으로 안전하게 적용하세요
""")


if __name__ == "__main__":
    main()