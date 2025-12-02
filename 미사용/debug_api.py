#!/usr/bin/env python3
"""
학생 관리 API 디버깅 스크립트
"""

import urllib.request
import urllib.parse
import json
import http.cookiejar

def test_admin_students_api():
    """관리자 학생 목록 API 테스트"""
    print("🔍 관리자 학생 목록 API 디버깅")
    print("=" * 50)
    
    # 쿠키 저장소 설정
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    urllib.request.install_opener(opener)
    
    try:
        # 1. 관리자 로그인
        print("1. 관리자 로그인 중...")
        login_data = urllib.parse.urlencode({
            'username': 'admin',
            'password': 'admin123'
        }).encode('utf-8')
        
        login_request = urllib.request.Request(
            'http://localhost:5000/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        login_response = urllib.request.urlopen(login_request)
        print(f"   로그인 응답 코드: {login_response.status}")
        
        if login_response.status != 200:
            print("❌ 로그인 실패")
            return False
        
        # 2. 학생 목록 API 호출
        print("2. 학생 목록 API 호출 중...")
        api_url = 'http://localhost:5000/api/admin/students?page=1&limit=20'
        
        try:
            api_request = urllib.request.Request(api_url)
            api_response = urllib.request.urlopen(api_request)
            
            print(f"   API 응답 코드: {api_response.status}")
            
            if api_response.status == 200:
                response_data = api_response.read().decode('utf-8')
                print(f"   응답 데이터 길이: {len(response_data)} 바이트")
                
                try:
                    json_data = json.loads(response_data)
                    print(f"   JSON 파싱 성공")
                    print(f"   응답 구조: {list(json_data.keys())}")
                    
                    if json_data.get('success'):
                        students = json_data.get('students', [])
                        print(f"✅ 학생 목록 조회 성공: {len(students)}명")
                        
                        for student in students:
                            print(f"     - {student.get('student_id')}: {student.get('name')} "
                                  f"({student.get('department')}) - {student.get('overall_completion_rate', 0)}%")
                        
                        print(f"   총 학생 수: {json_data.get('total', 0)}")
                        print(f"   학과 목록: {json_data.get('departments', [])}")
                        
                        return True
                    else:
                        print(f"❌ API 오류: {json_data.get('error', '알 수 없는 오류')}")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 오류: {e}")
                    print(f"   응답 내용 (처음 500자): {response_data[:500]}")
                    return False
            else:
                print(f"❌ API 호출 실패: HTTP {api_response.status}")
                return False
                
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP 오류: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            print(f"   오류 내용: {error_body}")
            return False
            
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        return False

def test_manual_route_access():
    """라우트 직접 접근 테스트"""
    print("\n📱 관리자 페이지 직접 접근 테스트")
    print("-" * 40)
    
    # 쿠키 저장소 설정
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    urllib.request.install_opener(opener)
    
    try:
        # 로그인
        login_data = urllib.parse.urlencode({
            'username': 'admin',
            'password': 'admin123'
        }).encode('utf-8')
        
        login_request = urllib.request.Request(
            'http://localhost:5000/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        urllib.request.urlopen(login_request)
        
        # 관리자 학생 페이지 접근
        page_request = urllib.request.Request('http://localhost:5000/admin/students')
        page_response = urllib.request.urlopen(page_request)
        
        print(f"✅ 관리자 학생 페이지 접근: HTTP {page_response.status}")
        
        page_content = page_response.read().decode('utf-8')
        
        # HTML 내용 확인
        if 'admin_students.html' in page_content or '학생 관리' in page_content:
            print("✅ 올바른 페이지 로드됨")
        else:
            print("⚠️ 예상과 다른 페이지 내용")
            
        if 'loadStudents' in page_content:
            print("✅ JavaScript 함수 포함됨")
        else:
            print("❌ JavaScript 함수 누락")
            
        return True
        
    except Exception as e:
        print(f"❌ 페이지 접근 오류: {e}")
        return False

def check_flask_routes():
    """Flask 라우트 확인"""
    print("\n🛠️ Flask 라우트 확인")
    print("-" * 30)
    
    try:
        # Flask 앱의 라우트를 확인하기 위한 간접적 방법
        routes_to_test = [
            '/admin/dashboard',
            '/admin/students', 
            '/api/admin/students'
        ]
        
        # 쿠키 저장소 설정
        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        urllib.request.install_opener(opener)
        
        # 로그인
        login_data = urllib.parse.urlencode({
            'username': 'admin',
            'password': 'admin123'
        }).encode('utf-8')
        
        login_request = urllib.request.Request(
            'http://localhost:5000/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        urllib.request.urlopen(login_request)
        
        for route in routes_to_test:
            try:
                request = urllib.request.Request(f'http://localhost:5000{route}')
                response = urllib.request.urlopen(request)
                print(f"✅ {route}: HTTP {response.status}")
            except urllib.error.HTTPError as e:
                print(f"❌ {route}: HTTP {e.code} - {e.reason}")
            except Exception as e:
                print(f"❌ {route}: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ 라우트 확인 오류: {e}")
        return False

def main():
    """메인 디버깅 함수"""
    print("🐛 학생 목록 로딩 문제 디버깅")
    print("=" * 60)
    
    tests = [
        ("관리자 학생 목록 API", test_admin_students_api),
        ("관리자 페이지 직접 접근", test_manual_route_access),
        ("Flask 라우트 확인", check_flask_routes),
    ]
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}] 테스트 중...")
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            print(f"결과: {status}")
        except Exception as e:
            print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    main()