import argparse
import csv
import sys
from typing import Dict, Tuple, Any
import mysql.connector
from mysql.connector import Error

# DB 설정 (update_db.py와 동일 구성 사용)
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

REQUIRED_COLUMNS = [
    'department', 'admission_year_from', 'admission_year_to',
    'grade_year', 'term', 'required_type',
    'course_code', 'course_name', 'credits', 'is_active'
]

VALID_REQUIRED_TYPES = {'전필', '전선'}

CANON_MAP = {
    '전공필수': '전필',
    '전공 선택': '전선',
    '전공선택': '전선',
    '필수': '전필',
    '선택': '전선',
}


def canon_required_type(value: str) -> str:
    v = (value or '').strip()
    if v in VALID_REQUIRED_TYPES:
        return v
    return CANON_MAP.get(v, v)


def coerce_int(v: Any) -> int:
    if v is None or v == '':
        return None
    try:
        val = int(str(v).strip())
        # MySQL YEAR 허용 범위(1901-2155)에 맞춰 9999는 2155로 치환
        if val == 9999:
            return 2155
        return val
    except Exception:
        raise ValueError(f"정수 변환 실패: {v}")


def coerce_float(v: Any) -> float:
    if v is None or v == '':
        return None
    try:
        return float(str(v).strip())
    except Exception:
        raise ValueError(f"실수 변환 실패: {v}")


def dedup_key(row: Dict[str, Any]) -> Tuple:
    return (
        row['department'],
        row['admission_year_from'],
        row['admission_year_to'],
        row['course_code'],
        row['required_type'],
    )


def is_better(lhs: Dict[str, Any], rhs: Dict[str, Any]) -> bool:
    """우선순위: grade_year가 있는 것이 우선, 더 작은 grade_year, 그리고 더 작은 term.
    lhs가 rhs보다 우선이면 True."""
    def score(r):
        gy = r.get('grade_year')
        tm = r.get('term')
        # None은 가장 뒤로
        gy_score = 999 if gy in (None, '') else int(gy)
        tm_score = 99 if tm in (None, '') else int(tm)
        return (gy_score, tm_score)

    return score(lhs) < score(rhs)


def validate_and_normalize(row: Dict[str, Any], line_no: int) -> Dict[str, Any]:
    for col in REQUIRED_COLUMNS:
        if col not in row:
            raise ValueError(f"{line_no}행: 필수 컬럼 누락: {col}")

    rtype = canon_required_type(row['required_type'])
    if rtype not in VALID_REQUIRED_TYPES:
        raise ValueError(f"{line_no}행: required_type 값 오류: {row['required_type']} -> 허용: {VALID_REQUIRED_TYPES}")

    dept = (row['department'] or '').strip()
    code = (row['course_code'] or '').strip()
    name = (row['course_name'] or '').strip()
    if not dept or not code or not name:
        raise ValueError(f"{line_no}행: department/course_code/course_name은 비어있을 수 없습니다.")

    out = {
        'department': dept,
        'admission_year_from': coerce_int(row['admission_year_from']),
        'admission_year_to': coerce_int(row['admission_year_to']),
        'grade_year': coerce_int(row['grade_year']),
        'term': coerce_int(row['term']),
        'required_type': rtype,
        'course_code': code,
        'course_name': name,
        'credits': coerce_float(row['credits']),
        'is_active': int(row['is_active']) if str(row['is_active']).strip() != '' else 1,
    }

    if out['admission_year_from'] is None or out['admission_year_to'] is None:
        raise ValueError(f"{line_no}행: admission_year_from/to는 필수 정수입니다.")
    if out['credits'] is None:
        raise ValueError(f"{line_no}행: credits는 필수 숫자입니다.")

    return out


def upsert_rows(rows: Dict[Tuple, Dict[str, Any]]):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        sql = (
            "INSERT INTO curriculum_courses (department, admission_year_from, admission_year_to, grade_year, term, required_type, course_code, course_name, credits, is_active) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON DUPLICATE KEY UPDATE course_name=VALUES(course_name), credits=VALUES(credits), is_active=VALUES(is_active), grade_year=VALUES(grade_year), term=VALUES(term)"
        )
        data = []
        for r in rows.values():
            data.append((
                r['department'], r['admission_year_from'], r['admission_year_to'], r.get('grade_year'), r.get('term'),
                r['required_type'], r['course_code'], r['course_name'], r['credits'], r['is_active']
            ))
        cur.executemany(sql, data)
        conn.commit()
        print(f"업서트 완료: {len(data)}건")
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
    dedup: Dict[Tuple, Dict[str, Any]] = {}
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"필드 누락: {missing}")
        for i, row in enumerate(reader, start=2):  # 1행은 헤더
            norm = validate_and_normalize(row, i)
            key = dedup_key(norm)
            if key not in dedup or is_better(norm, dedup[key]):
                dedup[key] = norm
            else:
                # 덜 우선인 중복은 건너뛰되 알림
                print(f"중복 스킵: {norm['department']} {norm['admission_year_from']}-{norm['admission_year_to']} {norm['required_type']} {norm['course_code']} (line {i})")
    return dedup


def main():
    parser = argparse.ArgumentParser(description='curriculum_courses CSV 업서트 도구')
    parser.add_argument('csv_files', nargs='+', help='업로드할 CSV 파일 경로(들)')
    args = parser.parse_args()

    merged: Dict[Tuple, Dict[str, Any]] = {}
    for p in args.csv_files:
        part = load_csv(p)
        for k, v in part.items():
            if k not in merged or is_better(v, merged[k]):
                merged[k] = v
    print(f"최종 업로드 대상: {len(merged)}건")
    upsert_rows(merged)


if __name__ == '__main__':
    main()
