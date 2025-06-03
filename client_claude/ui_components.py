# ui_components.py - UI 컴포넌트 생성 및 관리 (Claude 버전)

from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QComboBox, QTextEdit)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from config import COLORS, STYLES


class UIComponents:
    """UI 컴포넌트 생성 클래스 (Claude 버전)"""

    @staticmethod
    def create_title_frame():
        """타이틀 바 생성"""
        title_frame = QFrame()
        title_frame.setStyleSheet(STYLES['title_frame'])
        title_layout = QHBoxLayout(title_frame)

        title_label = QLabel("카카오톡 답변 도우미 (Claude)")
        title_label.setFont(QFont("맑은 고딕", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: #3C1E1E; padding: 5px;")

        close_button = QPushButton("×")
        close_button.setFixedSize(25, 25)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #3C1E1E;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

        return title_frame, close_button

    @staticmethod
    def create_status_label():
        """상태 표시 라벨 생성"""
        status_label = QLabel("카카오톡 창을 검색 중...")
        status_label.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 10px; padding: 5px;")
        return status_label

    @staticmethod
    def create_window_selection_frame():
        """창 선택 영역 생성"""
        frame = QFrame()
        frame.setStyleSheet(STYLES['window_frame'])
        layout = QVBoxLayout(frame)

        label = QLabel("카카오톡 대화창:")
        label.setFont(QFont("맑은 고딕", 9, QFont.Bold))
        layout.addWidget(label)

        # 창 선택 드롭다운
        window_combo = QComboBox()
        window_combo.setStyleSheet(STYLES['combo_box'])
        layout.addWidget(window_combo)

        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E8E8E8;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #D8D8D8;
            }}
        """)
        layout.addWidget(refresh_btn)

        return frame, window_combo, refresh_btn

    @staticmethod
    def create_chat_text_area():
        """대화 내용 입력 영역 생성"""
        chat_text = QTextEdit()
        chat_text.setPlaceholderText(
            "🤖 Claude AI 카카오톡 답변 도우미\n\n"
            "1. 카카오톡 창을 선택하세요\n"
            "2. '대화 가져오기' 버튼을 클릭하세요\n"
            "3. Claude가 생성한 답변을 선택하세요\n\n"
            "✨ Claude는 더 자연스럽고 맥락을 잘 이해하는\n"
            "   답변을 제공합니다!"
        )
        chat_text.setStyleSheet(STYLES['chat_text'])
        return chat_text

    @staticmethod
    def create_button_layout():
        """버튼 레이아웃 생성"""
        layout = QVBoxLayout()

        # 상단 버튼들
        top_layout = QHBoxLayout()

        # 대화 가져오기 버튼
        fetch_btn = QPushButton("📋 대화 가져오기")
        fetch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['secondary']};
                color: #2C5282;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary_hover']};
            }}
        """)

        # 자동 모드 버튼
        auto_btn = QPushButton("🔄 자동 모드")
        auto_btn.setCheckable(True)
        auto_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E8E8E8;
                color: {COLORS['text']};
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 10px;
            }}
            QPushButton:checked {{
                background-color: #68D391;
                color: white;
                font-weight: bold;
            }}
        """)

        top_layout.addWidget(fetch_btn)
        top_layout.addWidget(auto_btn)
        layout.addLayout(top_layout)

        # Claude 답변 생성 버튼 (더 눈에 띄게)
        generate_btn = QPushButton("🤖 Claude 답변 받기")
        generate_btn.setFont(QFont("맑은 고딕", 11, QFont.Bold))
        generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF6B35;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
                margin-top: 5px;
            }}
            QPushButton:hover {{
                background-color: #E55A2B;
            }}
        """)
        layout.addWidget(generate_btn)

        return layout, fetch_btn, auto_btn, generate_btn

    @staticmethod
    def create_suggestions_frame():
        """추천 답변 영역 생성 (Claude 버전)"""
        frame = QFrame()
        frame.setVisible(False)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['white']};
                border: 2px solid #FF6B35;
                border-radius: 8px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(frame)

        title = QLabel("🤖 Claude 답변 추천 (클릭하여 전송)")
        title.setFont(QFont("맑은 고딕", 9, QFont.Bold))
        title.setStyleSheet(f"color: #FF6B35; margin-bottom: 5px;")
        layout.addWidget(title)

        # 추천 답변 버튼들 (Claude 테마)
        suggestion_buttons = []
        button_configs = [
            ("😊", "#FFE5E0"),  # 따뜻한 오렌지 계열 - 긍정
            ("😐", "#F0F9FF"),  # 연한 파란색 - 중립
            ("😔", "#FFF0E6"),  # 연한 베이지색 - 부정
        ]

        for i, (emoji, color) in enumerate(button_configs):
            btn = QPushButton(f"{emoji} Claude 답변 생성 중...")
            btn.setFont(QFont("맑은 고딕", 9))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: {COLORS['text']};
                    border: 1px solid #FF6B35;
                    border-radius: 6px;
                    padding: 10px;
                    text-align: left;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: #FFD6CC;
                    border-color: #E55A2B;
                }}
            """)
            layout.addWidget(btn)
            suggestion_buttons.append(btn)

        return frame, suggestion_buttons

    @staticmethod
    def update_status_label(label, text, status_type="info"):
        """상태 라벨 업데이트"""
        color_map = {
            'info': COLORS['info'],
            'success': COLORS['success'],
            'error': COLORS['error'],
            'warning': COLORS['warning'],
        }

        color = color_map.get(status_type, COLORS['text_light'])
        label.setText(text)
        label.setStyleSheet(f"color: {color}; font-size: 10px; padding: 5px;")

    @staticmethod
    def set_main_window_style(widget):
        """메인 윈도우 스타일 설정 (Claude 테마)"""
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 240);
                border-radius: 10px;
                border: 2px solid #FF6B35;
            }}
        """)


# Claude 전용 색상 팔레트
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

# Claude 전용 스타일
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