# 졸업학점 관리 시스템

Python + MySQL 기반의 웹 시스템으로, 학생들의 학점 이수 현황을 자동 분석하고 졸업 요건 충족 여부를 관리하는 시스템입니다.

## 🚀 주요 기능

### 학생 기능
- **Excel 파일 업로드**: .xlsx 파일을 통한 학점 데이터 자동 추출
- **졸업요건 자동 분석**: 이수 현황과 졸업 요건 비교 분석
- **시각화 대시보드**: 이수율 차트와 상세 분석 결과 제공
- **알림 확인**: 관리자 발송 메시지 실시간 확인

### 관리자 기능
- **졸업요건 관리**: 학과별, 연도별 졸업 기준 CRUD
- **학생 현황 조회**: 필터링 기반 학생 데이터 검색
- **알림 시스템**: 개별/그룹/전체 대상 메시지 발송
- **통계 대시보드**: 학과별, 이수율별 통계 시각화

## 📁 프로젝트 구조

```
xlsx_project/
├── auth_system.py              # 인증 및 세션 관리
├── xlsx_parser_module.py       # Excel 파일 파싱 및 DB 저장
├── graduation_requirements_checker.py  # 졸업요건 분석
├── dashboard_renderer.py       # 시각화 대시보드
├── notification_system.py      # 알림 전송/조회
├── admin_api.py               # 관리자 API
├── database_schema.sql        # MySQL 스키마
├── requirements.txt           # Python 패키지 의존성
├── templates/                 # HTML 템플릿
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   └── admin_requirements.html
└── ex_1.xlsx                 # 샘플 Excel 파일
```

## 🛠️ 설치 및 실행

### 1. 환경 설정

```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 설정

```bash
# MySQL 접속
mysql -u root -p

# 데이터베이스 생성 및 스키마 실행
mysql> source database_schema.sql
```

### 3. 데이터베이스 연결 설정

각 Python 파일의 `db_config` 딕셔너리를 환경에 맞게 수정:

```python
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}
```

### 4. 애플리케이션 실행

```bash
# 인증 시스템 서버 실행
python auth_system.py
```

브라우저에서 `http://localhost:5000` 접속

## 📊 데이터베이스 스키마

### 주요 테이블
- `users`: 사용자 계정 (학생/관리자)
- `students`: 학생 개인정보 및 학적
- `course_records`: 수강 기록
- `graduation_requirements`: 졸업요건 기준
- `graduation_analysis`: 분석 결과
- `notifications`: 알림 발송 기록
- `notification_recipients`: 알림 수신 상태

## 🔧 모듈별 사용법

### 1. Excel 파일 파싱

```python
from xlsx_parser_module import process_excel_file

# Excel 파일 처리
success = process_excel_file('ex_1.xlsx', '2023001', db_config)
```

### 2. 졸업요건 분석

```python
from graduation_requirements_checker import analyze_student_graduation

# 학생 분석 실행
result = analyze_student_graduation('2023001', db_config)
```

### 3. 대시보드 렌더링

```python
from dashboard_renderer import render_student_dashboard

# 대시보드 HTML 생성
html = render_student_dashboard(analysis_result, use_plotly=True)
```

### 4. 알림 전송

```python
from notification_system import send_notification_to_students

# 전체 학생에게 알림 전송
result = send_notification_to_students(
    sender_id='admin',
    title='시스템 점검 안내',
    message='점검 시간: 오전 2-4시',
    target_type='all',
    db_config=db_config
)
```

## 👤 초기 계정

시스템 첫 실행 시 자동 생성되는 관리자 계정:
- **ID**: admin
- **비밀번호**: admin123

⚠️ **보안상 운영 환경에서는 반드시 비밀번호를 변경하세요.**

## 🔐 보안 기능

- 비밀번호 bcrypt 해시화
- 세션 기반 인증 (8시간 유지)
- 역할 기반 접근 제어 (RBAC)
- SQL 인젝션 방지
- XSS 방지를 위한 입력 검증

## 📈 지원하는 Excel 형식

시스템은 다음 필드를 자동으로 인식합니다:

**개인정보 필드:**
- 대학, 학과, 전공, 부전공, 다전공
- 과정, 입학일자, 학번, 성명
- 교과적용년도, 이수학기, 생년월일, 학년

**이수학점 필드:**
- 구분, 영역, 세부영역
- 년도, 학기, 교과목번호, 교과목명
- 학점, 이수구분, 성적

## 🎯 향후 개발 계획

- [ ] 이메일 알림 기능 강화
- [ ] 모바일 반응형 UI 개선
- [ ] 수강 추천 알고리즘 고도화
- [ ] REST API 문서화
- [ ] 단위 테스트 추가
- [ ] Docker 컨테이너화

## 🐛 문제 해결

### 자주 발생하는 오류

1. **MySQL 연결 실패**
   - MySQL 서버 실행 상태 확인
   - 연결 정보(host, user, password) 확인

2. **Excel 파일 파싱 오류**
   - 파일 형식이 .xlsx인지 확인
   - 필요한 컬럼명이 포함되어 있는지 확인

3. **패키지 설치 오류**
   - Python 버전 3.8 이상 사용 권장
   - 가상환경 활성화 상태 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 개발자

졸업학점 관리 시스템 개발팀
