# config.py - Claude API 버전 설정 (client_claude 디렉토리용)

# Anthropic API 키 설정
ANTHROPIC_API_KEY = ""  # 실제 API 키로 변경하세요 (예: "sk-ant-api03-...")

# UI 설정
WINDOW_WIDTH = 350
WINDOW_HEIGHT = 500
WINDOW_TITLE = '카카오톡 답변 추천 (Claude AI 버전)'

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

# Claude 설정
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # 기본 모델
CLAUDE_TEMPERATURE = 0.8
CLAUDE_MAX_TOKENS = 150  # Claude는 더 간결한 답변 가능
CLAUDE_N_SUGGESTIONS = 3

# Claude 모델 선택 옵션
CLAUDE_MODEL_OPTIONS = {
    "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (최신, 고성능)",
    "claude-3-5-haiku-20241022": "Claude 3.5 Haiku (빠름, 경제적)",
    "claude-3-opus-20240229": "Claude 3 Opus (최고 성능)",
}

# 고급 모드 설정
USE_KOKYUNGWOO_MODE = True  # True로 설정하면 고경우 모드 사용
ENABLE_MODEL_SELECTION = True  # 모델 선택 UI 표시 여부

# =====================================================
# 🆕 대화 파서 선택 설정
# =====================================================
PARSER_TYPE = "date"  # "count" 또는 "date"

# count: 최근 N개 메시지 기준 파싱 (chat_parser.py)
# date: 최근 하루 기준 파싱 (chat_date_parser.py)

# 개수 기반 파싱 설정 (PARSER_TYPE = "count"일 때)
MAX_RECENT_MESSAGES = 20  # 최근 몇 개 메시지까지 가져올지

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

# 고경우 모드 프롬프트 (Claude 최적화 버전)
KOKYUNGWOO_PROMPT = """당신은 고경우라는 친구의 말투로 카카오톡 대화에 답변해야 합니다.

🎯 고경우 핵심 특징:
• 매우 짧은 문장 (평균 5-8글자)
• 간결하고 직설적
• 친근한 반말 사용
• 자주 사용하는 줄임말과 특이한 표현들

✨ 필수 말투 요소:
1. 줄임말: "했어"→"햇어", "모르지"→"몰루", "있긴해"→"잇긴해"
2. 감정표현: ㅋㅋ, ㅠㅠ, ㅗㅜ, ㄷㄷ, ㅇㅇ, ㄴㄴ
3. 특이한 추임새: "야미", "홀리몰리", "요리조리"
4. 어미패턴: ~지, ~더라, ~구나, ~야?
5. 영어믹스: "Yum", "RIP", "hmm...", "Zzzz"

💬 답변 규칙:
- 15글자를 절대 넘지 않음
- 설명이나 부연설명 금지
- 한 글자 답변도 OK ("아", "음", ".")
- 상황에 맞는 직관적 반응

지금부터 고경우가 되어 대화에 답변해주세요. 긴 설명 없이 바로 고경우의 답변만 해주세요."""

# UI 색상 (Claude 테마)
COLORS = {
    'primary': '#FEE500',  # 카카오톡 노란색
    'primary_hover': '#E6CF00',
    'secondary': '#A3E1FF',  # 하늘색
    'secondary_hover': '#7DCFFF',
    'claude_orange': '#FF6B35',  # Claude 테마 오렌지
    'claude_orange_hover': '#E55A2B',
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

# UI 스타일 (Claude 테마)
STYLES = {
    'title_frame': f"""
        QFrame {{
            background-color: {COLORS['primary']};
            border-radius: 10px;
            border: 2px solid #FF6B35;
        }}
    """,

    'window_frame': f"""
        QFrame {{ 
            background-color: {COLORS['background']}; 
            border-radius: 5px; 
            padding: 8px;
            border: 1px solid #FF6B35;
        }}
    """,

    'chat_text': f"""
        QTextEdit {{
            background-color: {COLORS['white']};
            border: 2px solid #FF6B35;
            border-radius: 5px;
            padding: 8px;
            font-size: 10px;
            line-height: 1.4;
        }}
    """,

    'combo_box': f"""
        QComboBox {{
            padding: 8px;
            border: 1px solid #FF6B35;
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