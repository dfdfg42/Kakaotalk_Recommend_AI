# config.py - 설정 및 상수 (파서 선택 기능 추가)

# OpenAI API 키 설정
OPENAI_API_KEY = ""  # 실제 API 키로 변경하세요

# UI 설정
WINDOW_WIDTH = 350
WINDOW_HEIGHT = 500
WINDOW_TITLE = '카카오톡 답변 추천 (완전 자동화 버전)'

# 타이머 설정 (밀리초)
WINDOW_SCAN_INTERVAL = 10000  # 10초마다 창 스캔
CLIPBOARD_CHECK_INTERVAL = 3000  # 3초마다 클립보드 확인

# 카카오톡 대화 영역 클릭 위치 (비율)
CHAT_AREA_POSITIONS = [
    (0.5, 0.3),  # 중앙 상단
    (0.5, 0.4),  # 중앙
    (0.5, 0.5),  # 정중앙
    (0.4, 0.3),  # 좌측 상단
    (0.6, 0.3),  # 우측 상단
]

# 카카오톡 입력창 클릭 위치 (비율)
INPUT_AREA_POSITIONS = [
    (0.5, 0.85),  # 하단 중앙 (일반적)
    (0.5, 0.90),  # 하단 중앙 (더 아래)
    (0.5, 0.80),  # 하단 중앙 (위쪽)
    (0.3, 0.85),  # 하단 좌측
    (0.7, 0.85),  # 하단 우측
    (0.5, 0.75),  # 중하단
]

# 재시도 위치 (대화 가져오기 실패 시)
RETRY_POSITIONS = [(0.3, 0.3), (0.7, 0.3), (0.5, 0.6)]

# GPT 설정
GPT_MODEL = "gpt-3.5-turbo"
GPT_TEMPERATURE = 0.8
GPT_MAX_TOKENS = 1000
GPT_N_SUGGESTIONS = 3

# 파인튜닝된 모델 설정
USE_FINE_TUNED_MODEL = True # True로 설정하면 파인튜닝된 모델 사용
FINE_TUNED_MODEL_ID = ""  # 파인튜닝된 모델 ID (예: "ft:gpt-3.5-turbo-0125:...")

# =====================================================
# 🆕 대화 파서 선택 설정
# =====================================================
PARSER_TYPE = "count"  # "count" 또는 "date"

# count: 최근 N개 메시지 기준 파싱 (chat_parser.py)
# date: 최근 하루 기준 파싱 (chat_date_parser.py)

# 개수 기반 파싱 설정 (PARSER_TYPE = "count"일 때)
MAX_RECENT_MESSAGES = 10  # 최근 몇 개 메시지까지 가져올지

# 날짜 기반 파싱 설정 (PARSER_TYPE = "date"일 때)
DATE_LIMIT_HOURS = 24  # 최근 몇 시간까지 가져올지 (기본 24시간 = 하루)

# =====================================================

# 기본 모델용 시스템 프롬프트 - 긍정/중립/부정 구분
SYSTEM_PROMPT = """당신은 카카오톡 대화에 대한 자연스럽고 적절한 답변을 추천해주는 도우미입니다. 
다음 조건을 만족하는 답변 3개를 각각 하나씩만 생성해주세요:

1. 긍정적인 답변: 밝고 적극적인 반응
2. 중립적인 답변: 균형잡힌 무난한 반응  
3. 부정적인 답변: 소극적이거나 조심스러운 반응

각 답변은 간결하고 자연스러운 한국어로 작성하되, 각각 하나의 완성된 답변만 제시해주세요."""

# 고경우 기본 프롬프트 (톤별 지시사항은 런타임에 추가)
KOKYUNGWOO_PROMPT = """다음 카카오톡 대화에 마지막 말에 이어질 답변을 고경우의 말투로 답변해주세요.

절대 대답 앞에 카톡 시간을 붙이면 안돼

🎯 고경우 말투 특징 (필수 준수):

📏 문장 스타일:
- 매우 짧은 문장 
- 간결하고 직관적, 불필요한 설명 생략
- 주어, 조사 자주 생략
- 한 글자 답변도 자주 사용: "아", "음", ".", "?" 등

😂 감정 표현:
- 웃음: ㅋㅋ, ㅋㅎ (길게도: ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ)
- 슬픔/아쉬움: ㅠㅠ
- 짜증/답답함: ㅗㅜ
- 놀람: ㄷㄷ, ㄷㄷ...
- 동의: ㅇㅇ (응응)
- 부정: ㄴㄴ (노노)


🔚 어미 패턴:
- 평서문: "~지", "~더라", "~거든", "~구나"
- 의문문: "~야?", "~음?", "~지?"
- 감탄문: "~네!", "~구나!"

💬 대화 스타일:
- 반말 기본 (친구 사이)
- 솔직하고 직설적
- 장황한 설명 절대 안 함
- 상황에 따라 한 글자로도 답변

❌ 절대 금지사항:
- 정중한 존댓말 사용
- 표준어 완벽 사용
- "그렇습니다", "~입니다" 같은 격식체
- 과도한 설명이나 친절함
- 설명 텍스트나 번호 형태 답변

🚨 중요: 설명 없이 바로 고경우의 실제 답변만 하나 작성하세요!"""

# UI 색상
COLORS = {
    'primary': '#FEE500',  # 카카오톡 노란색
    'primary_hover': '#E6CF00',
    'secondary': '#A3E1FF',  # 하늘색
    'secondary_hover': '#7DCFFF',
    'success': '#38A169',  # 초록색
    'error': '#E53E3E',  # 빨간색
    'warning': '#D69E2E',  # 주황색
    'info': '#3182CE',  # 파란색
    'text': '#2D3748',  # 진한 회색
    'text_light': '#666',  # 연한 회색
    'background': '#F8F8F8',  # 배경
    'white': '#FFFFFF',
    'border': '#CCCCCC',
}

# UI 스타일
STYLES = {
    'title_frame': f"""
        QFrame {{
            background-color: {COLORS['primary']};
            border-radius: 10px;
        }}
    """,

    'window_frame': f"""
        QFrame {{ 
            background-color: {COLORS['background']}; 
            border-radius: 5px; 
            padding: 8px; 
        }}
    """,

    'chat_text': f"""
        QTextEdit {{
            background-color: {COLORS['white']};
            border: 1px solid {COLORS['border']};
            border-radius: 5px;
            padding: 8px;
            font-size: 10px;
            line-height: 1.4;
        }}
    """,

    'combo_box': f"""
        QComboBox {{
            padding: 8px;
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            background-color: {COLORS['white']};
            font-size: 10px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
    """,
}

# 최소 대화 내용 길이
MIN_CHAT_LENGTH = 10

# 지연 시간 (초)
DELAYS = {
    'click_stabilize': 0.2,
    'key_input': 0.01,
    'focus_wait': 0.3,
    'copy_wait': 0.5,
    'paste_wait': 0.3,
    'send_wait': 0.5,
}

# =====================================================