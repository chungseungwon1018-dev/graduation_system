import pandas as pd
import os

xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '연도별 졸업요건 정리.xlsx')

df = pd.read_excel(xlsx_path, header=0)
# 컬럼 소정리
cols = {c: c.strip() for c in df.columns}
# 기본 매핑
mapping = {
    '입학연도':'admission_year','학과':'department','카테고리':'category','영역':'area','세부영역':'sub_area','최저이수학점':'min_credits','상한학점':'max_credits'
}
new_cols = {}
for c in df.columns:
    key = c.strip()
    new_cols[c] = mapping.get(key, key)

df = df.rename(columns=new_cols)
# 필터링
df = df[df['admission_year'].notna() & df['department'].notna() & df['area'].notna() & df['min_credits'].notna()]

# 그룹 요약
group = df.groupby(['department','admission_year','category','area'], dropna=False).agg(
    min_credits=('min_credits','sum'),
    max_credits=('max_credits', lambda x: x.dropna().max() if x.dropna().size>0 else None),
    rows=('area','count')
).reset_index()

print('적용될 졸업요건 요약 (학과 / 연도 / 카테고리 / 영역):')
print(group.to_string(index=False))
print('\n총 레코드:', len(group))
