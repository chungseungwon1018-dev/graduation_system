#!/usr/bin/env python3
"""
학생 알림 시스템 테스트 스크립트
"""

import mysql.connector
import json
import logging
from datetime import datetime
from notification_system import send_notification_to_students

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 설정
db_config = {
    'host': '203.255.78.58',
    'port': 9003,
    'database': 'graduation_system',
    'user': 'user29',
    'password': '123'
}

def test_notification_api():
    """알림 API 테스트"""
    print("=" * 50)
    print("알림 시스템 테스트 시작")
    print("=" * 50)
    
    try:
        # 1. 테스트 알림 생성
        result = send_notification_to_students(
            sender_id='admin',
            title='테스트 알림',
            message='이것은 학생 인터페이스 테스트를 위한 알림입니다.\n\n새로운 알림 시스템이 정상적으로 작동하는지 확인하기 위한 메시지입니다.',
            target_type='all',
            is_urgent=False,
            db_config=db_config
        )
        
        if result.get('success'):
            print(f"✅ 일반 알림 전송 성공: {result.get('recipients_count', 0)}명에게 발송")
        else:
            print(f"❌ 일반 알림 전송 실패: {result.get('error', '알 수 없는 오류')}")
        
        # 2. 긴급 알림 생성
        urgent_result = send_notification_to_students(
            sender_id='admin',
            title='긴급 알림 - 졸업요건 변경',
            message='경영학과 2024년 입학생 대상으로 졸업요건이 변경되었습니다.\n\n변경사항:\n- 교양 필수학점: 15학점 → 18학점\n- 전공 선택학점: 21학점 → 24학점\n\n자세한 내용은 학과 홈페이지를 확인해주세요.',
            target_type='group',
            target_data={'department': '경영학과', 'admission_year': 2024},
            is_urgent=True,
            db_config=db_config
        )
        
        if urgent_result.get('success'):
            print(f"✅ 긴급 알림 전송 성공: {urgent_result.get('recipients_count', 0)}명에게 발송")
        else:
            print(f"❌ 긴급 알림 전송 실패: {urgent_result.get('error', '알 수 없는 오류')}")
        
        # 3. 알림 테이블 확인
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as count FROM notifications")
        notification_count = cursor.fetchone()['count']
        print(f"✅ 총 알림 개수: {notification_count}")
        
        cursor.execute("SELECT COUNT(*) as count FROM notification_recipients")
        recipient_count = cursor.fetchone()['count']
        print(f"✅ 총 수신자 레코드 개수: {recipient_count}")
        
        # 4. 최근 알림 내용 확인
        cursor.execute("""
            SELECT n.title, n.message, n.is_urgent, n.sent_at, COUNT(nr.id) as recipient_count
            FROM notifications n
            LEFT JOIN notification_recipients nr ON n.id = nr.notification_id
            GROUP BY n.id
            ORDER BY n.sent_at DESC
            LIMIT 3
        """)
        
        recent_notifications = cursor.fetchall()
        print(f"\n📢 최근 알림 {len(recent_notifications)}개:")
        for notif in recent_notifications:
            urgency = "🚨 긴급" if notif['is_urgent'] else "📢 일반"
            print(f"  - {urgency} {notif['title']} (수신자: {notif['recipient_count']}명)")
            print(f"    발송시간: {notif['sent_at']}")
            print(f"    내용: {notif['message'][:50]}...")
            print()
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 알림 시스템 테스트 실패: {e}")
        return False

def test_student_notification_data():
    """학생별 알림 데이터 확인"""
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        # 학생별 알림 통계
        cursor.execute("""
            SELECT 
                nr.recipient_id,
                COUNT(*) as total_notifications,
                SUM(CASE WHEN nr.is_read = 0 THEN 1 ELSE 0 END) as unread_count,
                MAX(n.sent_at) as latest_notification
            FROM notification_recipients nr
            JOIN notifications n ON nr.notification_id = n.id
            GROUP BY nr.recipient_id
            ORDER BY unread_count DESC, latest_notification DESC
            LIMIT 5
        """)
        
        student_stats = cursor.fetchall()
        
        print("\n👤 학생별 알림 현황 (상위 5명):")
        for stat in student_stats:
            print(f"  - {stat['recipient_id']}: 총 {stat['total_notifications']}개, 읽지않음 {stat['unread_count']}개")
            print(f"    최근 알림: {stat['latest_notification']}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 학생 알림 데이터 확인 실패: {e}")
        return False

def create_sample_notifications():
    """샘플 알림 생성"""
    print("\n📝 샘플 알림 생성 중...")
    
    sample_notifications = [
        {
            'title': '시스템 점검 안내',
            'message': '매주 일요일 오전 2시-4시 시스템 점검이 진행됩니다.\n점검 시간 중에는 시스템 이용이 제한됩니다.',
            'target_type': 'all',
            'is_urgent': False
        },
        {
            'title': '졸업 논문 제출 마감일 안내',
            'message': '4학년 학생들의 졸업 논문 제출 마감일이 다가왔습니다.\n\n제출 마감: 2025년 6월 15일\n제출 방법: 온라인 포털 시스템\n\n기한 내 제출하지 않으면 졸업이 연기될 수 있습니다.',
            'target_type': 'group',
            'target_data': {'grade': 4},
            'is_urgent': True
        },
        {
            'title': '신규 교양 과목 개설 안내',
            'message': '다음 학기 새로운 교양 과목이 개설됩니다.\n\n- AI와 사회 (3학점)\n- 창의적 글쓰기 (2학점)\n- 환경과 지속가능성 (3학점)\n\n수강 신청 시 참고하시기 바랍니다.',
            'target_type': 'all',
            'is_urgent': False
        }
    ]
    
    success_count = 0
    
    for notification in sample_notifications:
        try:
            result = send_notification_to_students(
                sender_id='admin',
                title=notification['title'],
                message=notification['message'],
                target_type=notification['target_type'],
                target_data=notification.get('target_data'),
                is_urgent=notification['is_urgent'],
                db_config=db_config
            )
            
            if result.get('success'):
                print(f"✅ '{notification['title']}' 전송 성공")
                success_count += 1
            else:
                print(f"❌ '{notification['title']}' 전송 실패")
                
        except Exception as e:
            print(f"❌ '{notification['title']}' 전송 중 오류: {e}")
    
    print(f"\n📊 샘플 알림 생성 완료: {success_count}/{len(sample_notifications)}개 성공")
    
    return success_count == len(sample_notifications)

def main():
    """메인 테스트 함수"""
    print("🔔 학생 알림 시스템 테스트")
    print("=" * 60)
    
    tests = [
        ("기본 알림 API 테스트", test_notification_api),
        ("학생 알림 데이터 확인", test_student_notification_data),
        ("샘플 알림 생성", create_sample_notifications),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}] 테스트 중...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n통과: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 모든 테스트가 통과했습니다!")
        print("\n💡 학생 대시보드 확인 방법:")
        print("1. 학생으로 로그인")
        print("2. 우상단 🔔 알림 아이콘 클릭")
        print("3. 알림 목록 및 읽음 처리 확인")
        print("4. '모든 알림 보기' 클릭하여 전체 알림 모달 확인")
    else:
        print(f"\n⚠️ {len(results) - passed}개의 테스트가 실패했습니다.")

if __name__ == "__main__":
    main()