import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

# DB 설정 (main_app.py와 동일)
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

migration_sql_path = os.path.join(os.path.dirname(__file__), 'graduation_requirements_migration.sql')


def column_exists(conn, table_schema, table_name, column_name):
    cursor = conn.cursor()
    query = ("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
             "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s")
    cursor.execute(query, (table_schema, table_name, column_name))
    cnt = cursor.fetchone()[0]
    cursor.close()
    return cnt > 0


def execute_sql_file(conn, sql_path):
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    # MySQL 버전 호환성: 일부 환경에서는 'ADD COLUMN IF NOT EXISTS'를 지원하지 않음
    # 이미 컬럼을 추가했으니 마이그레이션 파일의 해당 구문을 제거하여 실행합니다.
    import re
    sql_sanitized = re.sub(r"ALTER\s+TABLE\s+graduation_requirements\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS[^;]*;",
                           '', sql, flags=re.IGNORECASE)
    # None 리터럴이 SQL에 들어가 있으면 MySQL은 이를 인식하지 못하므로 NULL로 치환
    sql_sanitized = re.sub(r"\bNone\b", 'NULL', sql_sanitized)

    # admission_year가 NULL인 잘못된 INSERT 문을 제거
    import re as _re
    before_len = len(sql_sanitized)
    sql_sanitized = _re.sub(r"INSERT INTO\s+graduation_requirements[\s\S]*?VALUES\s*\(\s*'[^']*'\s*,\s*NULL[\s\S]*?;",
                            '', sql_sanitized, flags=_re.IGNORECASE)
    after_len = len(sql_sanitized)
    removed_bytes = before_len - after_len
    if removed_bytes > 0:
        print(f'Removed {removed_bytes} bytes of invalid INSERTs (admission_year NULL) from SQL before execution')

    cursor = conn.cursor()
    try:
        # Execute multi-statement SQL (sanitized)
        for result in cursor.execute(sql_sanitized, multi=True):
            if result.with_rows:
                _ = result.fetchall()
        conn.commit()
        return True, None
    except Error as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()


def main():
    print('DB에 연결 시도...')
    try:
        conn = mysql.connector.connect(**db_config)
        print('연결 성공')
    except Error as e:
        print(f'DB 연결 실패: {e}')
        return

    try:
        # 1) graduation_requirements 테이블 컬럼 점검
        print('graduation_requirements 테이블 컬럼 확인...')
        has_max = column_exists(conn, db_config['database'], 'graduation_requirements', 'max_credits')
        print('max_credits 존재 여부:', has_max)

        if not has_max:
            print('max_credits 컬럼이 없습니다. 추가합니다...')
            try:
                cursor = conn.cursor()
                cursor.execute("ALTER TABLE graduation_requirements ADD COLUMN max_credits DECIMAL(4,1) NULL AFTER required_credits;")
                conn.commit()
                cursor.close()
                print('max_credits 컬럼 추가 완료')
            except Error as e:
                print('컬럼 추가 중 오류:', e)
                conn.rollback()
                # 여긴 계속할 수 없음
                conn.close()
                return

        # 2) 대신: migration SQL 파일 대신 원본 엑셀을 읽어 유효한 행만 파라미터화하여 안전하게 INSERT 수행
        import pandas as pd
        xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_sample_1.xlsx')
        if not os.path.exists(xlsx_path):
            print('엑셀 파일을 찾을 수 없습니다:', xlsx_path)
            conn.close()
            return

        print('\n1. 원본 엑셀 파일 상세 분석...')
        print('1.1 첫 5행 데이터 확인 (헤더 없이):')
        df_raw = pd.read_excel(xlsx_path, header=None)
        print(df_raw.head().to_string())
        
        print('\n1.2 Non-NA 셀이 있는 컬럼 위치:')
        non_empty_cols = df_raw.count() > 0
        print(non_empty_cols[non_empty_cols].index.tolist())
        
        print('\n1.3 첫 번째 행:')
        print(df_raw.iloc[0].dropna().to_string())
        
        print('\n엑셀 파일의 구조가 예상과 다릅니다. 먼저 구조를 분석하고 매핑을 수정해야 합니다.')
        conn.close()
        return  # 여기서 중단하고 결과 확인 후 매핑 수정 필요
        for c in df.columns:
            key = c.strip()
            new_cols[c] = mapping.get(key, key)
            print(f'- 매핑: {c} → {new_cols[c]}')
        df = df.rename(columns=new_cols)

        # 필수 칼럼 필터
        print('\n3. 유효 데이터 필터링...')
        valid = df[df['admission_year'].notna() & df['department'].notna() & df['area'].notna() & df['min_credits'].notna()].copy()
        print(f'- 필터 후 행 수: {len(valid)}')
        
        print('\n4. 데이터 상세 분석:')
        # 입학년도별 통계
        print('\n4.1 입학년도별 레코드 수:')
        print(valid['admission_year'].value_counts().sort_index())
        
        # 카테고리/영역별 학점 요약
        print('\n4.2 카테고리/영역별 학점 요구사항:')
        summary = valid.groupby(['category', 'area'])[['min_credits', 'max_credits']].agg({
            'min_credits': ['count', 'sum'],
            'max_credits': ['count', 'sum']
        }).round(1)
        print(summary.to_string())
        
        # 세부영역이 있는 경우의 상세 내역
        print('\n4.3 세부영역별 상세 요구사항:')
        detailed = valid[valid['sub_area'].notna()][['category', 'area', 'sub_area', 'min_credits', 'max_credits']]
        print(detailed.to_string(index=False))
        
        print('\n4.4 전체 데이터 미리보기:')
        sample_cols = ['admission_year', 'department', 'category', 'area', 'sub_area', 'min_credits', 'max_credits']
        print(valid[sample_cols].head(10).to_string())

        # 백업 생성
        now_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'graduation_requirements_backup_{now_tag}'
        cursor = conn.cursor()
        cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM graduation_requirements")
        print('백업 테이블 생성:', backup_name)

        # 트랜잭션으로 일괄 INSERT
        try:
            insert_sql = ("INSERT INTO graduation_requirements "
                          "(department, admission_year, category, area, sub_area, required_credits, max_credits, description, is_active) "
                          "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                          "ON DUPLICATE KEY UPDATE required_credits=VALUES(required_credits), max_credits=VALUES(max_credits), description=VALUES(description), is_active=VALUES(is_active), updated_at=CURRENT_TIMESTAMP")

            for idx, row in valid.iterrows():
                ay = int(row['admission_year'])
                department = str(row['department'])
                category = str(row['category']) if pd.notna(row.get('category')) else '교양'
                area = str(row['area'])
                sub_area = str(row['sub_area']) if 'sub_area' in valid.columns and pd.notna(row.get('sub_area')) else None
                min_credits = float(row['min_credits'])
                max_credits = float(row['max_credits']) if 'max_credits' in valid.columns and pd.notna(row.get('max_credits')) else None
                description = f'최저이수학점: {min_credits}'
                if max_credits is not None:
                    description = f'최저이수학점: {min_credits}, 상한학점: {max_credits}'

                params = (department, ay, category, area, sub_area, min_credits, max_credits, description, True)
                cursor.execute(insert_sql, params)

            conn.commit()
            print('엑셀 기반 마이그레이션 적용 완료')
        except Error as e:
            conn.rollback()
            print('엑셀 기반 마이그레이션 중 오류:', e)
            cursor.close()
            conn.close()
            return

        # 3) 결과 확인: 총 레코드 수, 연도별 요약 등
        cursor.execute('SELECT COUNT(*) FROM graduation_requirements')
        total = cursor.fetchone()[0]
        print('graduation_requirements 총 레코드 수:', total)

        print('\n샘플(최신 20개):')
        cursor.execute("SELECT department, admission_year, category, area, sub_area, required_credits, max_credits FROM graduation_requirements ORDER BY admission_year DESC, category LIMIT 20")
        rows = cursor.fetchall()
        for r in rows:
            print(r)

        cursor.close()

    except Error as e:
        print('오류 발생:', e)
    finally:
        conn.close()
        print('DB 연결 종료')

if __name__ == '__main__':
    main()
