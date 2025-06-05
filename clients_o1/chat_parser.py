# chat_parser.py - 카카오톡 대화 파싱 및 최근 대화 추출 (개선된 버전)

import re
from datetime import datetime
from typing import List, Dict, Optional


class ChatMessage:
    """개별 채팅 메시지 클래스"""

    def __init__(self, sender: str, content: str, timestamp: str = None):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.raw_time = None

        # 시간 정보가 있으면 파싱
        if timestamp:
            self.raw_time = self._parse_time(timestamp)

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """시간 문자열을 datetime 객체로 변환"""
        try:
            # 다양한 시간 형식 처리
            time_patterns = [
                r'(\d{1,2}):(\d{2})',  # 오후 3:45, 오전 11:30
                r'(\d{1,2})시 (\d{1,2})분',  # 3시 45분
                r'(\d{4})\. (\d{1,2})\. (\d{1,2})\.',  # 2024. 1. 15.
            ]

            for pattern in time_patterns:
                if re.search(pattern, time_str):
                    # 간단한 시간 파싱 (실제로는 더 정교한 파싱 필요)
                    return datetime.now()  # 임시로 현재 시간 반환

            return None
        except:
            return None

    def __str__(self):
        if self.timestamp:
            return f"[{self.timestamp}] {self.sender}: {self.content}"
        else:
            return f"{self.sender}: {self.content}"


class KakaoTalkChatParser:
    """카카오톡 대화 파서 클래스 (개선된 버전)"""

    def __init__(self):
        # 카카오톡 메시지 패턴들
        self.message_patterns = [
            # 기본 패턴: [발신자] [시간] 메시지
            r'^(.+?)\s+(?:오전|오후)\s+(\d{1,2}:\d{2})\s*(.+)$',
            # 연속 메시지 패턴 (시간 없음)
            r'^(.+?)\s+(.+)$',
            # 시스템 메시지 패턴
            r'^(.+님이.+)$',
            # 단순 패턴
            r'^([^:]+):\s*(.+)$',
        ]

        # 필터링할 시스템 메시지들 (확장된 버전)
        self.system_patterns = [
            # 기존 패턴들
            r'.+님이 들어왔습니다',
            r'.+님이 나갔습니다',
            r'읽음\s*\d*',
            r'^\d+$',  # 숫자만 있는 행
            r'^$',  # 빈 행
            r'카카오톡',
            r'채팅방',
            r'^\s*$',  # 공백만 있는 행

            # 추가된 시스템 메시지 패턴들
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

        # 기존 시스템 메시지 패턴 확인
        for pattern in self.system_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True

        return False

    def parse_message_line(self, line: str) -> Optional[ChatMessage]:
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

                if len(groups) == 3:  # 발신자, 시간, 메시지
                    sender, timestamp, content = groups
                    # 메시지 내용이 실제로 있는지 확인
                    if content and content.strip():
                        # 메시지 내용에도 URL이 있는지 다시 한번 확인
                        if self.contains_url(content):
                            return None
                        return ChatMessage(
                            sender=sender.strip(),
                            content=content.strip(),
                            timestamp=timestamp.strip()
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
                            content=content.strip()
                        )

        # 패턴에 맞지 않는 경우, 이전 메시지의 연속으로 처리
        # (실제 구현에서는 이전 메시지와 합칠 수 있음)
        if len(line) > 5:  # 최소 길이 확인
            # URL이 포함된 연속 메시지도 제거
            if self.contains_url(line):
                return None
            return ChatMessage(
                sender="(연속)",
                content=line
            )

        return None

    def extract_recent_messages(self, chat_text: str, max_messages: int = 20) -> List[ChatMessage]:
        """채팅 텍스트에서 최근 메시지들을 추출 (개선된 필터링)"""
        lines = chat_text.split('\n')
        messages = []
        filtered_count = 0  # 필터링된 메시지 수 추적

        # 역순으로 처리 (최근 메시지부터)
        for line in reversed(lines):
            if len(messages) >= max_messages:
                break

            # 원본 라인이 시스템 메시지인지 먼저 확인
            if self.is_system_message(line):
                filtered_count += 1
                continue

            message = self.parse_message_line(line)
            if message and message.content:
                # 중복 메시지 확인
                if not self._is_duplicate_message(message, messages):
                    messages.append(message)

        # 시간순으로 정렬 (오래된 것부터)
        messages.reverse()

        # 필터링 통계 출력
        print(f"📊 대화 분석 완료: 총 {len(lines)}줄 중 {filtered_count}개 시스템 메시지/URL 제거, {len(messages)}개 메시지 추출")

        return messages

    def _is_duplicate_message(self, new_message: ChatMessage, existing_messages: List[ChatMessage]) -> bool:
        """중복 메시지 확인"""
        for existing in existing_messages:
            if (existing.sender == new_message.sender and
                    existing.content == new_message.content):
                return True
        return False

    def format_messages_for_gpt(self, messages: List[ChatMessage]) -> str:
        """GPT에 전송할 형식으로 메시지들을 포맷팅"""
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
                'preview': '대화가 없습니다.'
            }

        participants = list(set(msg.sender for msg in messages if msg.sender != "(연속)"))
        last_message = messages[-1] if messages else None

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
            'preview': '\n'.join(preview_lines)
        }


# 사용 예시 및 테스트 함수
def test_chat_parser():
    """파서 테스트 함수 (개선된 버전)"""
    sample_chat = """
    김철수 오후 2:30 안녕하세요!
    이영희 오후 2:31 네 안녕하세요
    김철수 오후 2:32 오늘 날씨가 정말 좋네요
    이영희님이 들어왔습니다
    이영희 오후 2:33 맞아요, 산책하기 좋은 날씨에요
    김철수 오후 2:34 혹시 시간 되시면 같이 산책할까요?
    이영희 오후 2:35 좋은 생각이네요!
    읽음 2
    김철수 오후 2:36 그럼 3시에 공원에서 만날까요?
    이영희 오후 2:37 네, 알겠습니다
    박민수 오후 2:38 이 링크 한번 봐보세요 https://example.com/test
    이영희 오후 2:39 감사합니다!
    사진을 저장했습니다
    김철수 오후 2:40 그럼 이따 뵙겠습니다
    """

    parser = KakaoTalkChatParser()
    messages = parser.extract_recent_messages(sample_chat, 20)

    print("=== 파싱된 메시지들 (URL 및 시스템 메시지 제거됨) ===")
    for msg in messages:
        print(msg)

    print("\n=== 대화 요약 ===")
    summary = parser.get_chat_summary(messages)
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== GPT 전송용 포맷 ===")
    formatted = parser.format_messages_for_gpt(messages)
    print(formatted)


if __name__ == "__main__":
    test_chat_parser()