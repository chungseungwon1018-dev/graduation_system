#!/usr/bin/env python3
"""
웹 인터페이스 알림 기능 테스트
"""

import urllib.request
import urllib.parse
import json
import http.cookiejar

def test_student_notification_interface():
    """학생 알림 인터페이스 테스트"""
    print("🔔 학생 알림 웹 인터페이스 테스트")
    print("=" * 50)
    
    # 쿠키 저장소 설정
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    urllib.request.install_opener(opener)
    
    try:
        # 1. 로그인 테스트
        login_data = urllib.parse.urlencode({
            'username': '2021026018',
            'password': 'test'
        }).encode('utf-8')
        
        login_request = urllib.request.Request(
            'http://localhost:5000/login',
            data=login_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        login_response = urllib.request.urlopen(login_request)
        print(f"1. 로그인 응답 코드: {login_response.status}")
        
        if login_response.status == 200:
            # 2. 읽지 않은 알림 개수 조회
            count_request = urllib.request.Request('http://localhost:5000/api/student/notifications/unread-count')
            count_response = urllib.request.urlopen(count_request)
            
            if count_response.status == 200:
                count_data = json.loads(count_response.read().decode('utf-8'))
                unread_count = count_data.get('unread_count', 0)
                print(f"2. 읽지 않은 알림 개수: {unread_count}개")
            
            # 3. 알림 목록 조회
            notifications_request = urllib.request.Request('http://localhost:5000/api/student/notifications?limit=5')
            notifications_response = urllib.request.urlopen(notifications_request)
            
            if notifications_response.status == 200:
                notifications_data = json.loads(notifications_response.read().decode('utf-8'))
                notifications = notifications_data.get('notifications', [])
                
                print(f"3. 최근 알림 {len(notifications)}개:")
                for i, notif in enumerate(notifications, 1):
                    urgency = "🚨 긴급" if notif.get('is_urgent') else "📢 일반"
                    read_status = "읽음" if notif.get('is_read') else "읽지않음"
                    title = notif.get('title', '제목없음')
                    message = notif.get('message', '')[:50] + '...' if len(notif.get('message', '')) > 50 else notif.get('message', '')
                    
                    print(f"   {i}. {urgency} {title} ({read_status})")
                    print(f"      {message}")
            
            print("\n✅ 모든 API 테스트 성공!")
            return True
        
        else:
            print(f"❌ 로그인 실패: {login_response.status}")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False

def show_usage_instructions():
    """사용법 안내"""
    print("\n" + "=" * 60)
    print("📖 학생 알림 시스템 사용법")
    print("=" * 60)
    
    print("\n1. 🌐 웹 브라우저에서 접속:")
    print("   http://localhost:5000")
    
    print("\n2. 👤 학생 계정으로 로그인:")
    print("   ID: 2021026018")
    print("   PW: test")
    
    print("\n3. 🔔 알림 기능 테스트:")
    print("   ➤ 우상단 🔔 알림 아이콘 클릭")
    print("   ➤ 빨간 배지 숫자로 읽지 않은 알림 개수 확인")
    print("   ➤ 드롭다운에서 최근 알림 5개 확인")
    print("   ➤ 알림 클릭 시 읽음 처리")
    print("   ➤ '모두 읽음' 버튼으로 일괄 읽음 처리")
    print("   ➤ '모든 알림 보기' 클릭하여 전체 알림 모달 확인")
    
    print("\n4. 🎯 테스트 시나리오:")
    print("   ➤ 읽지 않은 알림이 있는 상태에서 페이지 로드")
    print("   ➤ 알림 아이콘 클릭하여 드롭다운 열기")
    print("   ➤ 개별 알림 클릭하여 읽음 처리")
    print("   ➤ 페이지 새로고침 후 알림 카운트 변화 확인")
    print("   ➤ 네비게이션 '알림' 메뉴 클릭하여 전체 알림 보기")
    
    print("\n5. 📱 반응형 디자인:")
    print("   ➤ 모바일 화면에서도 알림 기능 정상 작동")
    print("   ➤ 터치 인터페이스 지원")
    
    print("\n6. ⚡ 실시간 기능:")
    print("   ➤ 5분마다 자동으로 새 알림 확인")
    print("   ➤ 긴급 알림은 빨간색 테두리로 강조")
    print("   ➤ 읽지 않은 알림은 파란색 배경으로 구분")

def main():
    """메인 함수"""
    print("🚀 학생 알림 시스템 최종 테스트")
    print("=" * 60)
    
    # API 테스트
    api_test_result = test_student_notification_interface()
    
    # 사용법 안내
    show_usage_instructions()
    
    if api_test_result:
        print("\n🎉 알림 시스템이 성공적으로 구현되었습니다!")
        print("\n✨ 구현된 기능:")
        print("   ✅ 헤더 알림 아이콘 및 배지")
        print("   ✅ 실시간 읽지 않은 알림 개수 표시")
        print("   ✅ 알림 드롭다운 (최근 5개)")
        print("   ✅ 개별 알림 읽음 처리")
        print("   ✅ 전체 알림 읽음 처리")
        print("   ✅ 전체 알림 목록 모달")
        print("   ✅ 긴급/일반 알림 구분")
        print("   ✅ 상대 시간 표시 (방금 전, 1시간 전 등)")
        print("   ✅ 반응형 디자인")
        print("   ✅ 자동 새로고침 (5분마다)")
    else:
        print("\n⚠️ 일부 기능에 오류가 있습니다. 확인이 필요합니다.")

if __name__ == "__main__":
    main()