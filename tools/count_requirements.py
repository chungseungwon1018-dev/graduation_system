import pandas as pd
import os

xlsx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '연도별 졸업요건 정리.xlsx')

df = pd.read_excel(xlsx_path, header=0)
print('원본 총 행수:', len(df))

# 컬럼 매핑 (간단하게)
mapping = {'입학연도':'admission_year','학과':'department','카테고리':'category','영역':'area','세부영역':'sub_area','최저이수학점':'min_credits','상한학점':'max_credits'}
new_cols = {}
for c in df.columns:
    key = c.strip()
    new_cols[c] = mapping.get(key, key)

df = df.rename(columns=new_cols)

# 필터 조건: admission_year, department, area, min_credits 존재
filtered = df[df['admission_year'].notna() & df['department'].notna() & df['area'].notna() & df['min_credits'].notna()]
print('필터(입학연도/학과/영역/최저학점 존재) 후 행수:', len(filtered))

# 그룹 수
group = filtered.groupby(['department','admission_year','category','area'], dropna=False).size().reset_index()
print('그룹(요약) 개수:', len(group))

# 출력 제외된 행 인덱스 예시 (최대 10)
excluded = df.index.difference(filtered.index)
print('제외된 행 수:', len(excluded))
print('제외된 행 예시(최대10):', list(excluded[:10]))

# 만약 원하시면 제외된 행의 내용 샘플 보여주기
if len(excluded)>0:
    print('\n제외된 행 샘플:')
    print(df.loc[excluded[:10], :])
