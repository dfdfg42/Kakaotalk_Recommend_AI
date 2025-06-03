# chat_date_parser.py - 날짜 기반 카카오톡 대화 파싱 (최근 하루) - Claude 버전

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class ChatMessage:
    """개별 채팅 메시지 클래스"""

    def __init__(self, sender: str, content: str, timestamp: str = None, parsed_time: datetime = None):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.raw_time = parsed_time  # 파싱된 datetime 객체

    def __str__(self):
        if self.timestamp:
            return f"[{self.timestamp}] {self.sender}: {self.content}"
        else:
            return f"{self.sender}: {self.content}"


class KakaoTalkDateParser:
    """날짜 기반 카카오톡 대화 파서 클래스 (최근 하루) - Claude 버전"""

    def __init__(self):
        # 카카오톡 메시지 패턴들
        self.message_patterns = [
            # 기본 패턴: [발신자] [시간] 메시지
            r'^(.+?)\s+(오전|오후)\s+(\d{1,2}:\d{2})\s*(.+)$',
            # 연속 메시지 패턴 (시간 없음)
            r'^(.+?)\s+(.+)$',
            # 시스템 메시지 패턴
            r'^(.+님이.+)$',
            # 단순 패턴
            r'^([^:]+):\s*(.+)$',
        ]

        # 날짜 패턴들
        self.date_patterns = [
            r'^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(.*)$',  # 2024년 1월 15일
            r'^(\d{1,2})월\s*(\d{1,2})일\s*(.*)$',  # 1월 15일
            r'^(오늘)$',  # 오늘
            r'^(어제)$',  # 어제
            r'^(그저께)$',  # 그저께
        ]

        # 필터링할 시스템 메시지들
        self.system_patterns = [
            r'.+님이 들어왔습니다',
            r'.+님이 나갔습니다',
            r'읽음\s*\d*',
            r'^\d+$',  # 숫자만 있는 행
            r'^$',  # 빈 행
            r'카카오톡',
            r'채팅방',
            r'^\s*$',  # 공백만 있는 행
            r'.+님을 초대했습니다',
            r'.+님이 초대되었습니다',
            r'.+님을 내보냈습니다',
            r'.+님이 방장으로 변경되었습니다',
            r'.+님이 관리자로 지정되었습니다',
            r'.+님의 관리자 권한이 해제되었습니다',
            r'사진을 저장했습니다',
            r'동영상을 저장했습니다',
            r'파일을 저장했습니다',
            r'음성메시지',
            r'음성 메시지',
            r'이모티콘',
            r'스티커',
            r'선물하기',
            r'송금하기',
            r'돈 보내기',
            r'위치 공유',
            r'연락처 공유',
            r'일정 공유',
            r'투표',
            r'공지사항',
            r'공지가 등록되었습니다',
            r'삭제된 메시지입니다',
            r'차단된 메시지입니다',
            r'신고된 메시지입니다',
            r'메시지가 삭제되었습니다',
            r'이 메시지는 삭제되었습니다',
            r'채팅방 이름이 변경되었습니다',
            r'채팅방 프로필이 변경되었습니다',
            r'채팅방 배경이 변경되었습니다',
            r'새로운 멤버가 추가되었습니다',
            r'멤버가 나갔습니다',
            r'보이스톡',
            r'페이스톡',
            r'화상통화',
            r'통화 시작',
            r'통화 종료',
            r'통화 연결',
            r'알림 설정',
            r'알림 해제',
            r'즐겨찾기 추가',
            r'즐겨찾기 해제',
            r'대화 내용을 저장했습니다',
            r'대화 내용이 저장되었습니다',
            r'메모가 저장되었습니다',
            r'캘린더에 추가되었습니다',
            r'일정이 생성되었습니다',
            r'리마인더가 설정되었습니다',
            r'프로필이 업데이트되었습니다',
            r'상태메시지가 변경되었습니다',
            r'생일 알림',
            r'친구 추가',
            r'친구 삭제',
            r'차단 해제',
            r'숨김 해제',
            r'대화방 잠금',
            r'대화방 잠금 해제',
            # 날짜/시간 구분선
            r'^\d{4}년\s+\d{1,2}월\s+\d{1,2}일',
            r'^\d{1,2}월\s+\d{1,2}일',
            r'오늘',
            r'어제',
            r'그저께',
            # 기타 시스템 알림
            r'새로운 기능',
            r'업데이트',
            r'버전',
            r'점검',
            r'서비스',
            r'서버',
            r'네트워크',
            r'연결',
            r'동기화',
            # 광고/스팸 관련
            r'광고',
            r'홍보',
            r'이벤트 참여',
            r'쿠폰',
            r'할인',
            r'무료 체험',
            r'당첨',
            r'추첨',
        ]

        # URL 패턴들
        self.url_patterns = [
            r'https?://[^\s]+',  # http://, https:// URL
            r'www\.[^\s]+',  # www로 시작하는 URL
            r'[a-zA-Z0-9][\w\.-]*\.[a-zA-Z]{2,}(?:/[^\s]*)?',  # 일반 도메인
            r'bit\.ly/[^\s]+',  # 단축 URL
            r'tinyurl\.com/[^\s]+',
            r'goo\.gl/[^\s]+',
            r't\.co/[^\s]+',
            r'youtu\.be/[^\s]+',
            r'youtube\.com/[^\s]+',
            r'naver\.me/[^\s]+',
            r'open\.kakao\.com/[^\s]+',  # 카카오톡 오픈 링크
            r'talk\.kakao\.com/[^\s]+',
            r'pf\.kakao\.com/[^\s]+',  # 카카오 플러스친구 링크
        ]

        # 현재 시간 기준
        self.now = datetime.now()
        self.today = self.now.date()
        self.yesterday = self.today - timedelta(days=1)

    def parse_date_line(self, line: str) -> Optional[datetime]:
        """날짜 라인을 파싱하여 datetime 객체 반환"""
        line = line.strip()

        for pattern in self.date_patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()

                if '년' in line and '월' in line and '일' in line:
                    # 2024년 1월 15일 형태
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    try:
                        return datetime(year, month, day)
                    except ValueError:
                        continue

                elif '월' in line and '일' in line:
                    # 1월 15일 형태 (현재 년도로 가정)
                    month, day = int(groups[0]), int(groups[1])
                    try:
                        return datetime(self.now.year, month, day)
                    except ValueError:
                        continue

                elif groups[0] == '오늘':
                    return datetime.combine(self.today, datetime.min.time())
                elif groups[0] == '어제':
                    return datetime.combine(self.yesterday, datetime.min.time())
                elif groups[0] == '그저께':
                    day_before_yesterday = self.today - timedelta(days=2)
                    return datetime.combine(day_before_yesterday, datetime.min.time())

        return None

    def parse_time(self, am_pm: str, time_str: str, base_date: datetime) -> datetime:
        """시간 문자열을 파싱하여 완전한 datetime 객체 생성"""
        try:
            hour, minute = map(int, time_str.split(':'))

            # 오후인 경우 12시간 추가 (단, 12시는 그대로)
            if am_pm == '오후' and hour != 12:
                hour += 12
            elif am_pm == '오전' and hour == 12:
                hour = 0

            return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except (ValueError, AttributeError):
            return base_date

    def contains_url(self, text: str) -> bool:
        """텍스트에 URL이 포함되어 있는지 확인"""
        for pattern in self.url_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_system_message(self, line: str) -> bool:
        """시스템 메시지인지 확인 (URL 포함 메시지도 시스템 메시지로 간주)"""
        line = line.strip()

        # 빈 줄이거나 너무 짧은 메시지
        if len(line) < 2:
            return True

        # URL이 포함된 메시지는 시스템 메시지로 간주
        if self.contains_url(line):
            return True

        # 날짜 라인은 시스템 메시지로 간주
        if self.parse_date_line(line):
            return True

        # 기존 시스템 메시지 패턴 확인
        for pattern in self.system_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True

        return False

    def is_within_last_day(self, message_time: datetime) -> bool:
        """메시지가 최근 하루 이내인지 확인"""
        if not message_time:
            return True  # 시간 정보가 없으면 포함

        time_diff = self.now - message_time
        return time_diff.total_seconds() <= 24 * 3600  # 24시간 이내

    def parse_message_line(self, line: str, current_date: datetime) -> Optional[ChatMessage]:
        """한 줄을 파싱해서 ChatMessage 객체 생성"""
        line = line.strip()

        # 시스템 메시지 필터링 (URL 포함 메시지도 여기서 걸러짐)
        if self.is_system_message(line):
            return None

        # 다양한 패턴으로 메시지 파싱 시도
        for pattern in self.message_patterns:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()

                if len(groups) == 4:  # 발신자, 오전/오후, 시간, 메시지
                    sender, am_pm, time_str, content = groups
                    if content and content.strip():
                        # 메시지 내용에 URL이 있는지 확인
                        if self.contains_url(content):
                            return None

                        # 완전한 시간 파싱
                        message_time = self.parse_time(am_pm, time_str, current_date)

                        # 최근 하루 이내 메시지인지 확인
                        if not self.is_within_last_day(message_time):
                            return None

                        return ChatMessage(
                            sender=sender.strip(),
                            content=content.strip(),
                            timestamp=f"{am_pm} {time_str}",
                            parsed_time=message_time
                        )

                elif len(groups) == 2:  # 발신자, 메시지 (또는 연속 메시지)
                    sender, content = groups
                    # 발신자 이름이 너무 길면 메시지의 일부일 가능성
                    if len(sender) < 20 and content and content.strip():
                        # 메시지 내용에 URL이 있는지 확인
                        if self.contains_url(content):
                            return None
                        return ChatMessage(
                            sender=sender.strip(),
                            content=content.strip(),
                            parsed_time=current_date
                        )

        # 패턴에 맞지 않는 경우, 이전 메시지의 연속으로 처리
        if len(line) > 5:  # 최소 길이 확인
            # URL이 포함된 연속 메시지도 제거
            if self.contains_url(line):
                return None
            return ChatMessage(
                sender="(연속)",
                content=line,
                parsed_time=current_date
            )

        return None

    def extract_last_day_messages(self, chat_text: str) -> List[ChatMessage]:
        """채팅 텍스트에서 최근 하루 메시지들을 추출"""
        lines = chat_text.split('\n')
        messages = []
        current_date = self.now  # 기본값은 현재 시간
        filtered_count = 0
        date_sections_found = 0

        print(f"📅 Claude - 날짜 기반 파싱 시작 - 기준 시간: {self.now.strftime('%Y-%m-%d %H:%M')}")

        # 정순으로 처리 (날짜 정보를 순차적으로 파악하기 위해)
        for i, line in enumerate(lines):
            # 날짜 라인 확인
            parsed_date = self.parse_date_line(line)
            if parsed_date:
                current_date = parsed_date
                date_sections_found += 1
                print(f"📆 날짜 섹션 발견: {parsed_date.strftime('%Y-%m-%d')} (라인 {i + 1})")
                continue

            # 시스템 메시지인지 확인
            if self.is_system_message(line):
                filtered_count += 1
                continue

            # 메시지 파싱
            message = self.parse_message_line(line, current_date)
            if message and message.content:
                # 최근 하루 이내 메시지인지 확인
                if self.is_within_last_day(message.raw_time):
                    # 중복 메시지 확인
                    if not self._is_duplicate_message(message, messages):
                        messages.append(message)
                else:
                    # 하루를 넘긴 메시지는 카운트만
                    filtered_count += 1

        # 시간순으로 정렬 (최신 메시지가 마지막에)
        messages.sort(key=lambda x: x.raw_time if x.raw_time else self.now)

        # 필터링 통계 출력
        print(f"📊 Claude 날짜 기반 분석 완료:")
        print(f"   - 총 라인 수: {len(lines)}")
        print(f"   - 날짜 섹션: {date_sections_found}개")
        print(f"   - 필터링됨: {filtered_count}개 (시스템 메시지/URL/하루 초과)")
        print(f"   - 추출됨: {len(messages)}개 (최근 24시간 이내)")

        return messages

    def _is_duplicate_message(self, new_message: ChatMessage, existing_messages: List[ChatMessage]) -> bool:
        """중복 메시지 확인"""
        for existing in existing_messages:
            if (existing.sender == new_message.sender and
                    existing.content == new_message.content and
                    existing.raw_time and new_message.raw_time and
                    abs((existing.raw_time - new_message.raw_time).total_seconds()) < 60):  # 1분 이내 같은 내용
                return True
        return False

    def format_messages_for_gpt(self, messages: List[ChatMessage]) -> str:
        """Claude에 전송할 형식으로 메시지들을 포맷팅"""
        if not messages:
            return ""

        formatted_lines = []
        for message in messages:
            if message.timestamp:
                formatted_lines.append(f"{message.sender} [{message.timestamp}]: {message.content}")
            else:
                formatted_lines.append(f"{message.sender}: {message.content}")

        return '\n'.join(formatted_lines)

    def get_chat_summary(self, messages: List[ChatMessage]) -> Dict:
        """대화 요약 정보 생성"""
        if not messages:
            return {
                'total_messages': 0,
                'participants': [],
                'last_sender': None,
                'preview': '최근 하루 대화가 없습니다.',
                'time_range': '없음'
            }

        participants = list(set(msg.sender for msg in messages if msg.sender != "(연속)"))
        last_message = messages[-1] if messages else None

        # 시간 범위 계산
        times = [msg.raw_time for msg in messages if msg.raw_time]
        time_range = "시간 정보 없음"
        if times:
            earliest = min(times)
            latest = max(times)
            time_range = f"{earliest.strftime('%H:%M')} ~ {latest.strftime('%H:%M')}"

        # 미리보기 텍스트 생성
        preview_messages = messages[-3:] if len(messages) >= 3 else messages
        preview_lines = []
        for msg in preview_messages:
            preview_text = msg.content[:30] + "..." if len(msg.content) > 30 else msg.content
            preview_lines.append(f"{msg.sender}: {preview_text}")

        return {
            'total_messages': len(messages),
            'participants': participants,
            'last_sender': last_message.sender if last_message else None,
            'preview': '\n'.join(preview_lines),
            'time_range': time_range
        }


# 사용 예시 및 테스트 함수
def test_date_parser():
    """날짜 파서 테스트 함수 (Claude 버전)"""
    sample_chat = """
    2024년 6월 1일
    김철수 오전 9:30 좋은 아침이에요!
    이영희 오전 9:31 네 안녕하세요
    김철수님이 들어왔습니다
    김철수 오후 2:32 점심 맛있게 드셨나요?
    이영희 오후 2:33 네, 감사합니다
    박민수 오후 3:15 이 링크 봐보세요 https://example.com
    읽음 2
    김철수 오후 6:45 퇴근하시나요?
    이영희 오후 6:46 네, 이제 퇴근합니다
    어제
    김철수 오전 10:00 어제 회의 어떠셨나요?
    이영희 오전 10:01 좋았습니다
    """

    parser = KakaoTalkDateParser()
    messages = parser.extract_last_day_messages(sample_chat)

    print("=== Claude - 최근 하루 메시지들 (날짜 기반 필터링) ===")
    for msg in messages:
        time_info = f" ({msg.raw_time.strftime('%Y-%m-%d %H:%M')})" if msg.raw_time else ""
        print(f"{msg}{time_info}")

    print("\n=== 대화 요약 ===")
    summary = parser.get_chat_summary(messages)
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== Claude 전송용 포맷 ===")
    formatted = parser.format_messages_for_gpt(messages)
    print(formatted)


if __name__ == "__main__":
    test_date_parser()