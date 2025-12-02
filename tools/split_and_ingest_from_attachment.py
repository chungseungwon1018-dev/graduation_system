import csv
import os
import sys
from typing import List, Dict
import argparse

CURR_HEADER = ['department','admission_year_from','admission_year_to','grade_year','term','required_type','course_code','course_name','credits','is_active']
RECOG_HEADER = ['department','admission_year_from','admission_year_to','rule_type','source_college','source_department','required_type_source','course_code','course_name','recognized_type','is_active','notes']

PHRASE = '타학과(부, 전공)전공선택 인정 교과목'


def split_file(src_path: str, out_dir: str) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    curr_rows: List[List[str]] = []
    recog_rows: List[List[str]] = []

    with open(src_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Scan rows: curriculum rows have department in first cell; recognition rows have phrase in 4th cell
    for r in rows:
        if not r:
            continue
        # Normalize length
        while len(r) < 12:
            r.append('')
        dept = (r[0] or '').strip()
        if dept:
            if dept.lower() == 'department':
                continue  # skip original header
            # curriculum row
            # take first 10 cols, strip spaces in course_code
            cr = [c.strip() for c in r[:10]]
            if cr[6]:
                cr[6] = cr[6].replace(' ', '')
            curr_rows.append(cr)
        else:
            # recognition rows: expect phrase in col3 or col4
            phrase = ''.join(r[3:5]).strip()
            if PHRASE in phrase:
                source_dept = (r[5] or '').strip()
                course_code = (r[6] or '').strip()
                course_name = (r[7] or '').strip()
                credits = (r[8] or '').strip() or '3'
                is_active = (r[9] or '').strip() or '1'
                # default meta
                recog_rows.append([
                    '경영정보학과','2018','2021','개별과목','',source_dept,'전선',course_code,course_name,'전선',is_active,''
                ])
                # Also add for 2022
                recog_rows.append([
                    '경영정보학과','2022','2022','개별과목','',source_dept,'전선',course_code,course_name,'전선',is_active,''
                ])
                # And for 2023+
                recog_rows.append([
                    '경영정보학과','2023','9999','개별과목','',source_dept,'전선',course_code,course_name,'전선',is_active,''
                ])
            elif any(x.strip() for x in r):
                # possible rule line: "경영대학에서 개설되는 모든 전공필수과목" in last col
                tail = ''.join(r[11:]).strip() + ''.join(r[3:]).strip()
                if '경영대학에서 개설되는 모든 전공필수과목' in tail:
                    # add three rule rows for ranges
                    for yr_from, yr_to in [('2018','2021'),('2022','2022'),('2023','9999')]:
                        recog_rows.append([
                            '경영정보학과', yr_from, yr_to, '규칙', '경영대학', '', '전필', '', '', '전선', '1', '경영대학 전공필수 전선 인정'
                        ])
                # else ignore

    # Write outputs
    curr_path = os.path.join(out_dir, 'curriculum_from_attachment.csv')
    recog_path = os.path.join(out_dir, 'recognition_from_attachment.csv')
    with open(curr_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(CURR_HEADER)
        w.writerows(curr_rows)
    with open(recog_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(RECOG_HEADER)
        w.writerows(recog_rows)
    return {'curriculum': curr_path, 'recognition': recog_path}


def main():
    ap = argparse.ArgumentParser(description='첨부 혼합 CSV를 커리큘럼/인정 CSV로 분리')
    ap.add_argument('src', help='원본 CSV 경로')
    ap.add_argument('--out-dir', default='tools/_split_out', help='출력 디렉토리')
    args = ap.parse_args()

    paths = split_file(args.src, args.out_dir)
    print('생성 파일:', paths)


if __name__ == '__main__':
    main()
