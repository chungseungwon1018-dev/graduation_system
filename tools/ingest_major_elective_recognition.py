import argparse
import csv
import sys
from typing import Dict, Tuple, Any
import mysql.connector
from mysql.connector import Error

# DB 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

REQUIRED_COLUMNS = [
    'department','admission_year_from','admission_year_to','rule_type',
    'source_college','source_department','required_type_source',
    'course_code','course_name','recognized_type','is_active','notes'
]

VALID_RULE_TYPES = {'규칙','개별과목'}
VALID_REQUIRED_SOURCE = {'전필','전선','기타',''}
VALID_RECOGNIZED = {'전선'}


def coerce_int(v: Any):
    if v is None or v == '':
        return None
    try:
        val = int(str(v).strip())
        if val == 9999:
            return 2155
        return val
    except Exception:
        raise ValueError(f"정수 변환 실패: {v}")


def validate_and_normalize(row: Dict[str, Any], line_no: int) -> Dict[str, Any]:
    for col in REQUIRED_COLUMNS:
        if col not in row:
            raise ValueError(f"{line_no}행: 필수 컬럼 누락: {col}")

    rt = (row['rule_type'] or '').strip()
    if rt not in VALID_RULE_TYPES:
        raise ValueError(f"{line_no}행: rule_type 오류: {rt}")

    rec = (row['recognized_type'] or '').strip()
    if rec not in VALID_RECOGNIZED:
        raise ValueError(f"{line_no}행: recognized_type 오류: {rec}")

    rsrc = (row['required_type_source'] or '').strip()
    if rsrc not in VALID_REQUIRED_SOURCE:
        raise ValueError(f"{line_no}행: required_type_source 오류: {rsrc}")

    dept = (row['department'] or '').strip()
    scoll = (row['source_college'] or '').strip() or None
    sdept = (row['source_department'] or '').strip() or None
    code = (row['course_code'] or '').strip() or None
    name = (row['course_name'] or '').strip() or None

    out = {
        'department': dept,
        'admission_year_from': coerce_int(row['admission_year_from']),
        'admission_year_to': coerce_int(row['admission_year_to']),
        'rule_type': rt,
        'source_college': scoll,
        'source_department': sdept,
        'required_type_source': rsrc or None,
        'course_code': code,
        'course_name': name,
        'recognized_type': rec,
        'is_active': int(row['is_active']) if str(row['is_active']).strip() != '' else 1,
        'notes': (row['notes'] or '').strip() or None,
    }

    if not out['department']:
        raise ValueError(f"{line_no}행: department는 필수")
    if out['admission_year_from'] is None or out['admission_year_to'] is None:
        raise ValueError(f"{line_no}행: admission_year_from/to는 필수")

    if rt == '규칙':
        if not out['source_college'] and not out['source_department']:
            raise ValueError(f"{line_no}행: 규칙형은 source_college 또는 source_department 중 하나가 필요")
    else:  # 개별과목
        if not out['course_code']:
            # 코드 없는 행은 스킵하도록 상위에서 처리할 수 있게 마크
            out['__skip__'] = True

    return out


def upsert_rows(rows: Dict[Tuple, Dict[str, Any]]):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        sql = (
            "INSERT INTO major_elective_recognition (department, admission_year_from, admission_year_to, rule_type, source_college, source_department, required_type_source, course_code, course_name, recognized_type, is_active, notes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        data = []
        for r in rows.values():
            data.append((
                r['department'], r['admission_year_from'], r['admission_year_to'], r['rule_type'],
                r['source_college'], r['source_department'], r['required_type_source'], r['course_code'], r['course_name'],
                r['recognized_type'], r['is_active'], r['notes']
            ))
        cur.executemany(sql, data)
        conn.commit()
        print(f"삽입 완료: {len(data)}건")
    except Error as e:
        print(f"DB 오류: {e}")
        sys.exit(1)
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def load_csv(path: str) -> Dict[Tuple, Dict[str, Any]]:
    print(f"CSV 읽는 중: {path}")
    rows: Dict[Tuple, Dict[str, Any]] = {}
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"필드 누락: {missing}")
        for i, row in enumerate(reader, start=2):
            norm = validate_and_normalize(row, i)
            if norm.get('__skip__'):
                print(f"코드 없음 스킵: {row.get('source_department','')} {row.get('course_name','')}(line {i})")
                continue
            key = (i,)
            rows[key] = norm
    return rows


def main():
    parser = argparse.ArgumentParser(description='major_elective_recognition CSV 적재 도구')
    parser.add_argument('csv_files', nargs='+', help='CSV 파일 경로')
    args = parser.parse_args()

    merged: Dict[Tuple, Dict[str, Any]] = {}
    for p in args.csv_files:
        part = load_csv(p)
        merged.update(part)
    print(f"최종 삽입 대상: {len(merged)}건")
    upsert_rows(merged)


if __name__ == '__main__':
    main()
