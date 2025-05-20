import sys
import os
import pyperclip
import openai
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLabel, QFrame)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor
import pywinauto

# OpenAI API 키 설정 (환경 변수에서 가져오거나 직접 입력)
# openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.api_key = "your-api-key-here"  # 실제 사용 시 이 부분을 수정하세요


class KakaoTalkAssistant(QWidget):
    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.setWindowTitle('카카오톡 답변 추천')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 창 크기 및 위치
        self.resize(300, 400)
        self.position_window()

        # UI 초기화
        self.init_ui()

        # 드래그 관련 변수
        self.old_pos = None
        self.dragging = False

        # 카카오톡 창 핸들 (처음에는 None)
        self.kakao_window = None

        # 자동으로 클립보드 내용 확인 타이머
        self.clip_timer = QTimer(self)
        self.clip_timer.timeout.connect(self.check_clipboard)
        self.clip_timer.start(2000)  # 2초마다 확인

        # 마지막으로 처리한 클립보드 내용
        self.last_clipboard = ""

    def position_window(self):
        # 화면 오른쪽에 배치
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width() - 20,
                  screen_geometry.height() // 2 - self.height() // 2)

    def init_ui(self):
        # 전체 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 타이틀 바 프레임
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #FEE500; border-radius: 10px;")
        title_layout = QHBoxLayout(title_frame)

        # 타이틀 라벨
        title_label = QLabel("카카오톡 답변 추천")
        title_label.setFont(QFont("맑은 고딕", 10, QFont.Bold))
        title_label.setStyleSheet("color: #3C1E1E;")

        # 닫기 버튼
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #FEE500;
                color: #3C1E1E;
                font-weight: bold;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #E6CF00;
            }
        """)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

        # 대화 입력 영역
        self.chat_text = QTextEdit()
        self.chat_text.setPlaceholderText("카카오톡 대화를 복사하여 붙여넣거나 자동으로 가져올 때까지 기다리세요...")
        self.chat_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        # 답변 추천 버튼
        generate_button = QPushButton("답변 추천 받기")
        generate_button.setFont(QFont("맑은 고딕", 10))
        generate_button.setStyleSheet("""
            QPushButton {
                background-color: #FEE500;
                color: #3C1E1E;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #E6CF00;
            }
        """)
        generate_button.clicked.connect(self.generate_suggestions)

        # 자동 복사 옵션
        auto_copy_layout = QHBoxLayout()
        self.auto_copy_button = QPushButton("자동 가져오기")
        self.auto_copy_button.setCheckable(True)
        self.auto_copy_button.setStyleSheet("""
            QPushButton {
                background-color: #EEEEEE;
                color: #3C1E1E;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:checked {
                background-color: #A3E1FF;
            }
        """)
        self.auto_copy_button.clicked.connect(self.toggle_auto_copy)

        auto_copy_layout.addWidget(self.auto_copy_button)
        auto_copy_layout.addStretch()

        # 추천 답변 영역 (처음에는 숨김)
        self.suggestions_frame = QFrame()
        self.suggestions_frame.setVisible(False)
        self.suggestions_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
            }
        """)

        suggestions_layout = QVBoxLayout(self.suggestions_frame)
        suggestions_layout.setContentsMargins(5, 5, 5, 5)

        # 추천 답변 버튼들
        self.suggestion_buttons = []
        for i in range(3):
            button = QPushButton(f"추천 답변 {i + 1}")
            button.setFont(QFont("맑은 고딕", 9))
            button.setStyleSheet("""
                QPushButton {
                    background-color: #F2F2F2;
                    color: #3C1E1E;
                    border: 1px solid #DDDDDD;
                    border-radius: 5px;
                    padding: 8px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #E6E6E6;
                }
            """)
            button.clicked.connect(lambda checked, idx=i: self.use_suggestion(idx))
            suggestions_layout.addWidget(button)
            self.suggestion_buttons.append(button)

        # 레이아웃에 위젯 추가
        main_layout.addWidget(title_frame)
        main_layout.addWidget(self.chat_text)
        main_layout.addLayout(auto_copy_layout)
        main_layout.addWidget(generate_button)
        main_layout.addWidget(self.suggestions_frame)

        self.setLayout(main_layout)

        # 배경 스타일 설정
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 220);
                border-radius: 10px;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.pos() + delta)
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def toggle_auto_copy(self):
        if self.auto_copy_button.isChecked():
            # 카카오톡 창 찾기 시도
            try:
                self.find_kakaotalk_window()
                if not self.kakao_window:
                    self.auto_copy_button.setChecked(False)
            except Exception as e:
                print(f"카카오톡 창을 찾는 중 오류 발생: {e}")
                self.auto_copy_button.setChecked(False)

    def find_kakaotalk_window(self):
        """카카오톡 창을 찾아 저장"""
        try:
            # pywinauto를 사용하여 카카오톡 창을 찾음
            app = pywinauto.Application(backend="uia").connect(title_re=".*카카오톡.*")
            windows = app.windows()

            # 카카오톡 창 중에서 채팅 창을 식별
            for w in windows:
                if "카카오톡" in w.window_text() and w.is_visible():
                    self.kakao_window = w
                    print(f"카카오톡 창을 찾았습니다: {w.window_text()}")
                    return True

            print("카카오톡 창을 찾을 수 없습니다.")
            return False
        except Exception as e:
            print(f"카카오톡 창 찾기 오류: {e}")
            return False

    def check_clipboard(self):
        """클립보드 내용을 확인하고 변경되었으면 텍스트 영역에 반영"""
        if not self.auto_copy_button.isChecked():
            return

        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard and current_clipboard != self.last_clipboard:
                self.last_clipboard = current_clipboard
                self.chat_text.setPlainText(current_clipboard)
        except Exception as e:
            print(f"클립보드 확인 중 오류: {e}")

    def generate_suggestions(self):
        """OpenAI API를 통해 답변 추천 생성"""
        chat_text = self.chat_text.toPlainText().strip()
        if not chat_text:
            return

        try:
            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 카카오톡 대화에 대한 답변을 추천해주는 도우미입니다. 한국어로 자연스럽고 적절한 답변 3가지를 제시해주세요."},
                    {"role": "user", "content": f"다음 카카오톡 대화에 대한 적절한 답변을 추천해주세요:\n\n{chat_text}"}
                ],
                n=3,
                temperature=0.7
            )

            # 응답 처리
            suggestions = [choice.message.content for choice in response.choices]

            # UI에 표시
            self.display_suggestions(suggestions)

        except Exception as e:
            print(f"답변 생성 중 오류: {e}")
            # 에러 처리 (UI에 표시 등)

    def display_suggestions(self, suggestions):
        """생성된 추천 답변을 UI에 표시"""
        # 추천 답변 프레임 표시
        self.suggestions_frame.setVisible(True)

        # 각 버튼에 추천 답변 설정
        for i, suggestion in enumerate(suggestions):
            if i < len(self.suggestion_buttons):
                # 답변이 너무 길면 자르기
                display_text = suggestion[:100] + "..." if len(suggestion) > 100 else suggestion
                self.suggestion_buttons[i].setText(display_text)
                self.suggestion_buttons[i].setToolTip(suggestion)  # 전체 텍스트는 툴팁으로 표시

                # 데이터 저장 (클릭 시 사용)
                self.suggestion_buttons[i].setProperty("full_text", suggestion)

    def use_suggestion(self, index):
        """선택한 추천 답변을 사용 (클립보드에 복사 또는 카카오톡에 붙여넣기)"""
        if index >= len(self.suggestion_buttons):
            return

        # 전체 텍스트 가져오기
        full_text = self.suggestion_buttons[index].property("full_text")
        if not full_text:
            return

        # 클립보드에 복사
        pyperclip.copy(full_text)

        # 자동 붙여넣기가 활성화되고 카카오톡 창이 있으면 붙여넣기
        if self.auto_copy_button.isChecked() and self.kakao_window:
            try:
                # 카카오톡 창을 활성화
                self.kakao_window.set_focus()

                # 편집 영역에 붙여넣기 (Ctrl+V)
                pywinauto.keyboard.send_keys('^v')

                # 엔터 키 보내지는 않음 (사용자가 직접 확인 후 전송)

            except Exception as e:
                print(f"자동 붙여넣기 중 오류: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KakaoTalkAssistant()
    window.show()
    sys.exit(app.exec_())