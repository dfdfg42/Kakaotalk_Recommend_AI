# config.py - 설정 및 상수

# OpenAI API 키 설정
OPENAI_API_KEY = "your-api-key-here"  # 실제 API 키로 변경하세요

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
GPT_MAX_TOKENS = 80
GPT_N_SUGGESTIONS = 3

# 시스템 프롬프트
SYSTEM_PROMPT = """당신은 카카오톡 대화에 대한 자연스럽고 적절한 답변을 추천해주는 도우미입니다. 다음 조건을 만족하는 답변 3개를 생성해주세요:
1. 각각 다른 톤(정중함, 친근함, 재미있음)
2. 간결하고 자연스러운 한국어
3. 상황에 맞는 적절한 반응"""

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