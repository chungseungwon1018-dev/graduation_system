import os
import sys
import json
import mysql.connector
from enhanced_xlsx_parser import process_excel_file_enhanced

DB_CONFIG = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

SAMPLES = [
    ('샘플파일/report_1764415240667_정승원.xlsx', '2021026017'),
    ('샘플파일/report_1759295962875_이서아.xlsx', '2021026018'),
]

KEY_FIELDS = [
    'name','department','major','grade','curriculum_year',
    'major_required_credits','major_elective_credits','general_elective_credits'
]

def fetch_student_row(student_id: str):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

if __name__ == '__main__':
    results = []
    for path, sid in SAMPLES:
        if not os.path.exists(path):
            print(f"[SKIP] File not found: {path}")
            continue
        print(f"\n=== Processing {path} for student {sid} ===")
        ok, warnings = process_excel_file_enhanced(path, sid, DB_CONFIG)
        print(f"process ok={ok}, warnings={warnings}")
        row = fetch_student_row(sid)
        print("DB row:")
        if not row:
            print("  <no row>")
            continue
        for k in KEY_FIELDS:
            print(f"  {k}: {row.get(k)}")
        results.append((path, sid, ok, warnings, {k: row.get(k) for k in KEY_FIELDS}))
    # save summary
    with open('tools/verify_summary.json','w',encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nSummary written to tools/verify_summary.json")
