import mysql.connector
from mysql.connector import Error
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self, db_config: Dict[str, str], email_config: Optional[Dict[str, str]] = None):
        self.db_config = db_config
        self.email_config = email_config or {}
        self.connection = None
    
    def connect_db(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            logger.info("MySQL 데이터베이스 연결 성공")
        except Error as e:
            logger.error(f"MySQL 연결 오류: {e}")
            raise
    
    def disconnect_db(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL 연결 해제")
    
    def send_notification(self, sender_id: str, title: str, message: str, 
                         target_type: str = 'individual', target_recipients: List[str] = None,
                         target_filter: Dict = None, is_urgent: bool = False) -> Dict:
        """
        알림 전송
        
        Args:
            sender_id: 발송자 ID (관리자)
            title: 알림 제목
            message: 알림 내용
            target_type: 'individual', 'group', 'all' 중 하나
            target_recipients: individual일 때 수신자 목록
            target_filter: group일 때 필터 조건 (학과, 학년 등)
            is_urgent: 긴급 알림 여부
        """
        try:
            cursor = self.connection.cursor()
            
            notification_query = """
            INSERT INTO notifications (sender_id, title, message, target_type, 
                                    target_filter, is_urgent, sent_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            
            filter_json = json.dumps(target_filter) if target_filter else None
            
            cursor.execute(notification_query, (
                sender_id, title, message, target_type, 
                filter_json, is_urgent
            ))
            
            notification_id = cursor.lastrowid
            
            recipients = self._get_target_recipients(target_type, target_recipients, target_filter)
            
            if not recipients:
                self.connection.rollback()
                return {"success": False, "error": "수신자를 찾을 수 없습니다."}
            
            recipient_query = """
            INSERT INTO notification_recipients (notification_id, recipient_id)
            VALUES (%s, %s)
            """
            
            recipient_data = [(notification_id, recipient) for recipient in recipients]
            cursor.executemany(recipient_query, recipient_data)
            
            self.connection.commit()
            
            if self.email_config and is_urgent:
                self._send_email_notifications(recipients, title, message)
            
            logger.info(f"알림 전송 완료: {len(recipients)}명에게 발송")
            
            return {
                "success": True,
                "notification_id": notification_id,
                "recipients_count": len(recipients),
                "recipients": recipients
            }
            
        except Error as e:
            self.connection.rollback()
            logger.error(f"알림 전송 오류: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if cursor:
                cursor.close()
    
    def _get_target_recipients(self, target_type: str, target_recipients: List[str] = None, 
                              target_filter: Dict = None) -> List[str]:
        """대상 수신자 목록 조회"""
        try:
            cursor = self.connection.cursor()
            
            if target_type == 'individual':
                return target_recipients or []
            
            elif target_type == 'all':
                query = "SELECT username FROM users WHERE role = 'student' AND is_active = TRUE"
                cursor.execute(query)
                
            elif target_type == 'group' and target_filter:
                conditions = []
                params = []
                
                base_query = """
                SELECT u.username FROM users u
                JOIN students s ON u.username = s.student_id
                WHERE u.role = 'student' AND u.is_active = TRUE
                """
                
                if target_filter.get('department'):
                    conditions.append("s.department = %s")
                    params.append(target_filter['department'])
                
                if target_filter.get('grade'):
                    conditions.append("s.grade = %s")
                    params.append(target_filter['grade'])
                
                if target_filter.get('admission_year'):
                    conditions.append("YEAR(s.admission_date) = %s")
                    params.append(target_filter['admission_year'])
                
                if target_filter.get('completion_rate_below'):
                    conditions.append("""
                        s.student_id IN (
                            SELECT student_id FROM graduation_analysis 
                            WHERE overall_completion_rate < %s
                        )
                    """)
                    params.append(target_filter['completion_rate_below'])
                
                if conditions:
                    query = base_query + " AND " + " AND ".join(conditions)
                else:
                    query = base_query
                
                cursor.execute(query, params)
            
            else:
                return []
            
            results = cursor.fetchall()
            cursor.close()
            
            return [row[0] for row in results]
            
        except Error as e:
            logger.error(f"수신자 조회 오류: {e}")
            return []
    
    def _send_email_notifications(self, recipients: List[str], title: str, message: str):
        """이메일 알림 전송 (긴급 알림용)"""
        if not self.email_config:
            return
        
        try:
            smtp_server = self.email_config.get('smtp_server')
            smtp_port = self.email_config.get('smtp_port', 587)
            sender_email = self.email_config.get('sender_email')
            sender_password = self.email_config.get('sender_password')
            
            if not all([smtp_server, sender_email, sender_password]):
                logger.warning("이메일 설정이 불완전하여 이메일 전송을 건너뜁니다.")
                return
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                
                for recipient in recipients:
                    recipient_email = self._get_student_email(recipient)
                    if recipient_email:
                        msg = MimeMultipart()
                        msg['From'] = sender_email
                        msg['To'] = recipient_email
                        msg['Subject'] = f"[긴급] {title}"
                        
                        body = f"""
                        안녕하세요, {recipient}님.
                        
                        긴급 알림이 도착했습니다.
                        
                        제목: {title}
                        내용: {message}
                        
                        자세한 내용은 졸업학점 관리 시스템에 로그인하여 확인해주세요.
                        
                        감사합니다.
                        """
                        
                        msg.attach(MimeText(body, 'plain', 'utf-8'))
                        server.send_message(msg)
            
            logger.info(f"긴급 이메일 알림 전송 완료: {len(recipients)}명")
            
        except Exception as e:
            logger.error(f"이메일 전송 오류: {e}")
    
    def _get_student_email(self, student_id: str) -> Optional[str]:
        """학생 이메일 주소 조회 (실제 구현에서는 학생 테이블에 이메일 필드 추가 필요)"""
        return f"{student_id}@university.edu"
    
    def get_notifications_for_user(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        """사용자의 알림 목록 조회"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT n.id, n.title, n.message, n.is_urgent, n.sent_at,
                   nr.is_read, nr.read_at
            FROM notifications n
            JOIN notification_recipients nr ON n.id = nr.notification_id
            WHERE nr.recipient_id = %s
            """
            
            params = [user_id]
            
            if unread_only:
                query += " AND nr.is_read = FALSE"
            
            query += " ORDER BY n.sent_at DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Error as e:
            logger.error(f"알림 조회 오류: {e}")
            return []
    
    def mark_notification_as_read(self, notification_id: int, user_id: str) -> bool:
        """알림을 읽음으로 표시"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            UPDATE notification_recipients 
            SET is_read = TRUE, read_at = NOW()
            WHERE notification_id = %s AND recipient_id = %s
            """
            
            cursor.execute(query, (notification_id, user_id))
            self.connection.commit()
            
            success = cursor.rowcount > 0
            cursor.close()
            
            if success:
                logger.info(f"알림 읽음 처리: 알림 ID {notification_id}, 사용자 {user_id}")
            
            return success
            
        except Error as e:
            logger.error(f"알림 읽음 처리 오류: {e}")
            self.connection.rollback()
            return False
    
    def get_unread_count(self, user_id: str) -> int:
        """사용자의 읽지 않은 알림 개수 조회"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT COUNT(*) FROM notification_recipients 
            WHERE recipient_id = %s AND is_read = FALSE
            """
            
            cursor.execute(query, (user_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            
            return count
            
        except Error as e:
            logger.error(f"읽지 않은 알림 개수 조회 오류: {e}")
            return 0
    
    def get_notification_statistics(self, sender_id: str = None) -> Dict:
        """알림 통계 조회 (관리자용)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            stats = {}
            
            base_condition = ""
            params = []
            
            if sender_id:
                base_condition = "WHERE sender_id = %s"
                params = [sender_id]
            
            total_query = f"SELECT COUNT(*) as total FROM notifications {base_condition}"
            cursor.execute(total_query, params)
            stats['total_notifications'] = cursor.fetchone()['total']
            
            read_query = f"""
            SELECT COUNT(DISTINCT nr.notification_id) as read_count
            FROM notification_recipients nr
            JOIN notifications n ON nr.notification_id = n.id
            {base_condition.replace('sender_id', 'n.sender_id') if base_condition else ''}
            AND nr.is_read = TRUE
            """
            cursor.execute(read_query, params)
            stats['read_notifications'] = cursor.fetchone()['read_count']
            
            recent_query = f"""
            SELECT COUNT(*) as recent_count
            FROM notifications 
            {base_condition}
            {'AND' if base_condition else 'WHERE'} sent_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            cursor.execute(recent_query, params)
            stats['recent_notifications'] = cursor.fetchone()['recent_count']
            
            urgent_query = f"""
            SELECT COUNT(*) as urgent_count
            FROM notifications 
            {base_condition}
            {'AND' if base_condition else 'WHERE'} is_urgent = TRUE
            """
            cursor.execute(urgent_query, params)
            stats['urgent_notifications'] = cursor.fetchone()['urgent_count']
            
            cursor.close()
            
            return stats
            
        except Error as e:
            logger.error(f"알림 통계 조회 오류: {e}")
            return {}
    
    def delete_notification(self, notification_id: int, sender_id: str) -> bool:
        """알림 삭제 (발송자만 가능)"""
        try:
            cursor = self.connection.cursor()
            
            # 먼저 알림이 해당 발송자의 것인지 확인
            check_query = "SELECT id FROM notifications WHERE id = %s AND sender_id = %s"
            cursor.execute(check_query, (notification_id, sender_id))
            
            if not cursor.fetchone():
                logger.warning(f"알림 삭제 권한 없음: ID {notification_id}, 발송자 {sender_id}")
                cursor.close()
                return False
            
            # 관련 수신자 레코드 먼저 삭제
            delete_recipients_query = "DELETE FROM notification_recipients WHERE notification_id = %s"
            cursor.execute(delete_recipients_query, (notification_id,))
            recipients_deleted = cursor.rowcount
            
            # 알림 본체 삭제
            delete_notification_query = "DELETE FROM notifications WHERE id = %s AND sender_id = %s"
            cursor.execute(delete_notification_query, (notification_id, sender_id))
            
            success = cursor.rowcount > 0
            self.connection.commit()
            cursor.close()
            
            if success:
                logger.info(f"알림 삭제 완료: ID {notification_id}, 수신자 레코드 {recipients_deleted}개 삭제")
            else:
                logger.warning(f"알림 삭제 실패: ID {notification_id}")
            
            return success
            
        except Error as e:
            logger.error(f"알림 삭제 오류: {e}")
            if self.connection:
                self.connection.rollback()
            return False

def send_notification_to_students(sender_id: str, title: str, message: str,
                                 target_type: str = 'all', target_data: Union[List[str], Dict] = None,
                                 is_urgent: bool = False, db_config: Dict[str, str] = None) -> Dict:
    """편의 함수: 학생들에게 알림 전송"""
    notification_system = NotificationSystem(db_config)
    
    try:
        notification_system.connect_db()
        
        if target_type == 'individual':
            result = notification_system.send_notification(
                sender_id, title, message, target_type, 
                target_recipients=target_data, is_urgent=is_urgent
            )
        elif target_type == 'group':
            result = notification_system.send_notification(
                sender_id, title, message, target_type,
                target_filter=target_data, is_urgent=is_urgent
            )
        else:  # 'all'
            result = notification_system.send_notification(
                sender_id, title, message, target_type, is_urgent=is_urgent
            )
        
        return result
        
    except Exception as e:
        logger.error(f"알림 전송 중 오류 발생: {e}")
        return {"success": False, "error": str(e)}
    finally:
        notification_system.disconnect_db()

def get_user_notifications(user_id: str, unread_only: bool = False, 
                          db_config: Dict[str, str] = None) -> List[Dict]:
    """편의 함수: 사용자 알림 조회"""
    notification_system = NotificationSystem(db_config)
    
    try:
        notification_system.connect_db()
        return notification_system.get_notifications_for_user(user_id, unread_only)
    except Exception as e:
        logger.error(f"알림 조회 중 오류 발생: {e}")
        return []
    finally:
        notification_system.disconnect_db()

if __name__ == "__main__":
    db_config = {
        'host': '203.255.78.58',
        'port': 9003,
        'database': 'graduation_system',
        'user': 'user29',
        'password': '123'
    }
    
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'system@university.edu',
        'sender_password': 'password'
    }
    
    # 테스트: 전체 학생에게 일반 알림 전송
    result = send_notification_to_students(
        sender_id='admin',
        title='시스템 점검 안내',
        message='시스템 점검으로 인해 내일 오전 2시-4시 서비스가 중단됩니다.',
        target_type='all',
        db_config=db_config
    )
    
    print(f"알림 전송 결과: {result}")
    
    # 테스트: 특정 학과 학생들에게 긴급 알림 전송
    result = send_notification_to_students(
        sender_id='admin',
        title='졸업요건 변경 안내',
        message='컴퓨터공학과 졸업요건이 변경되었습니다. 확인 바랍니다.',
        target_type='group',
        target_data={'department': '컴퓨터공학과'},
        is_urgent=True,
        db_config=db_config
    )
    
    print(f"긴급 알림 전송 결과: {result}")
    
    # 테스트: 사용자 알림 조회
    notifications = get_user_notifications('2023001', unread_only=True, db_config=db_config)
    print(f"읽지 않은 알림 개수: {len(notifications)}")