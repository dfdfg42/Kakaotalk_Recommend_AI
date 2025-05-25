import os
import sys
import pyperclip
import openai
import json
import time
import traceback
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QLabel, QFrame, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor
import win32gui
import win32con
import win32process
import win32clipboard
import ctypes
from ctypes import wintypes

from openai import OpenAI

# OpenAI API 키 설정
client = OpenAI(api_key="" )



class SafeWindowHandler:
    """안전한 윈도우 핸들링 클래스"""

    @staticmethod
    def safe_get_window_text(hwnd):
        """안전하게 윈도우 제목 가져오기"""
        try:
            length = win32gui.GetWindowTextLength(hwnd)
            if length == 0:
                return ""

            buffer = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value
        except Exception as e:
            print(f"윈도우 제목 가져오기 실패: {e}")
            return ""

    @staticmethod
    def get_window_rect(hwnd):
        """윈도우 크기와 위치 가져오기"""
        try:
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            return {
                'left': rect.left,
                'top': rect.top,
                'right': rect.right,
                'bottom': rect.bottom,
                'width': rect.right - rect.left,
                'height': rect.bottom - rect.top
            }
        except Exception as e:
            print(f"윈도우 크기 가져오기 실패: {e}")
            return None

    @staticmethod
    def click_window_area(hwnd, x_ratio=0.5, y_ratio=0.4):
        """윈도우 내 특정 비율 위치 클릭"""
        try:
            rect = SafeWindowHandler.get_window_rect(hwnd)
            if not rect:
                return False

            # 클릭할 절대 좌표 계산
            click_x = rect['left'] + int(rect['width'] * x_ratio)
            click_y = rect['top'] + int(rect['height'] * y_ratio)

            # 창을 앞으로 가져오기
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)

            # 마우스 클릭
            ctypes.windll.user32.SetCursorPos(click_x, click_y)
            time.sleep(0.1)

            # 마우스 왼쪽 버튼 클릭
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP

            time.sleep(0.2)
            return True

        except Exception as e:
            print(f"윈도우 클릭 실패: {e}")
            return False

    @staticmethod
    def find_chat_area_and_click(hwnd):
        """카카오톡 대화 영역을 찾아서 클릭"""
        try:
            rect = SafeWindowHandler.get_window_rect(hwnd)
            if not rect:
                return False

            # 카카오톡 창의 구조 분석
            # 일반적으로 대화 내용은 창의 중앙~상단 부분에 위치

            # 여러 위치를 시도해보기
            click_positions = [
                (0.5, 0.3),  # 중앙 상단
                (0.5, 0.4),  # 중앙
                (0.5, 0.5),  # 정중앙
                (0.4, 0.3),  # 좌측 상단
                (0.6, 0.3),  # 우측 상단
            ]

            for x_ratio, y_ratio in click_positions:
                if SafeWindowHandler.click_window_area(hwnd, x_ratio, y_ratio):
                    # 클릭 후 잠시 기다리고 테스트
                    time.sleep(0.2)

                    # Ctrl+A를 눌러서 선택이 되는지 테스트
                    if SafeWindowHandler.safe_send_keys("^a"):
                        time.sleep(0.1)
                        # 선택된 내용이 있는지 간접적으로 확인
                        # (실제로는 Ctrl+C 후 클립보드 확인으로 검증)
                        return True

            return False

        except Exception as e:
            print(f"대화 영역 찾기 실패: {e}")
            return False

    @staticmethod
    def safe_get_process_name(hwnd):
        """안전하게 프로세스 이름 가져오기"""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_handle = ctypes.windll.kernel32.OpenProcess(
                0x0400 | 0x0010,  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
                False,
                pid
            )

            if process_handle:
                buffer = ctypes.create_unicode_buffer(260)
                size = ctypes.sizeof(buffer)
                ctypes.windll.psapi.GetProcessImageFileNameW(
                    process_handle, buffer, size
                )
                ctypes.windll.kernel32.CloseHandle(process_handle)

                if buffer.value:
                    return os.path.basename(buffer.value).lower()
        except Exception as e:
            print(f"프로세스 이름 가져오기 실패: {e}")

        return ""

    @staticmethod
    def safe_send_keys(keys, hwnd=None):
        """안전한 키 입력"""
        try:
            if hwnd:
                # 창이 여전히 유효한지 확인
                if not win32gui.IsWindow(hwnd):
                    return False

                # 창을 앞으로 가져오기
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)

            # 키 입력
            if keys == "^a":  # Ctrl+A
                ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
                ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)  # A down
                ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)  # A up
                ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            elif keys == "^c":  # Ctrl+C
                ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
                ctypes.windll.user32.keybd_event(0x43, 0, 0, 0)  # C down
                ctypes.windll.user32.keybd_event(0x43, 0, 2, 0)  # C up
                ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            elif keys == "^v":  # Ctrl+V
                ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
                ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)  # V down
                ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)  # V up
                ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up

            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"키 입력 실패: {e}")
            return False


class WindowScanThread(QThread):
    """윈도우 스캔을 위한 별도 스레드"""
    windows_found = pyqtSignal(list)

    def run(self):
        """카카오톡 창들을 스캔"""
        try:
            windows = []

            def enum_callback(hwnd, param):
                try:
                    if not win32gui.IsWindowVisible(hwnd):
                        return True

                    title = SafeWindowHandler.safe_get_window_text(hwnd)
                    if not title:
                        return True

                    process_name = SafeWindowHandler.safe_get_process_name(hwnd)

                    # 카카오톡 관련 창인지 확인
                    if ('kakaotalk' in process_name or
                            'kakao' in process_name or
                            '카카오톡' in title):
                        windows.append({
                            'hwnd': hwnd,
                            'title': title,
                            'process': process_name
                        })

                except Exception as e:
                    print(f"창 열거 중 오류: {e}")

                return True

            win32gui.EnumWindows(enum_callback, None)
            self.windows_found.emit(windows)

        except Exception as e:
            print(f"윈도우 스캔 스레드 오류: {e}")
            self.windows_found.emit([])


class StableKakaoTalkAssistant(QWidget):
    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.setWindowTitle('카카오톡 답변 추천 (안정화 버전)')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 창 크기 및 위치
        self.resize(350, 450)
        self.position_window()

        # 변수 초기화
        self.kakao_windows = []
        self.selected_window = None
        self.old_pos = None
        self.dragging = False
        self.last_clipboard = ""

        # UI 초기화
        self.init_ui()

        # 스캔 스레드
        self.scan_thread = WindowScanThread()
        self.scan_thread.windows_found.connect(self.on_windows_found)

        # 타이머들
        self.setup_timers()

        # 초기 스캔
        self.scan_kakao_windows()

    def position_window(self):
        """화면 오른쪽에 배치"""
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width() - 20,
                  screen_geometry.height() // 2 - self.height() // 2)

    def setup_timers(self):
        """타이머 설정"""
        # 윈도우 스캔 타이머
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.scan_kakao_windows)
        self.scan_timer.start(10000)  # 10초마다 스캔 (빈도 줄임)

        # 클립보드 확인 타이머
        self.clip_timer = QTimer(self)
        self.clip_timer.timeout.connect(self.check_clipboard)

    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 타이틀 바
        title_frame = self.create_title_frame()
        main_layout.addWidget(title_frame)

        # 상태 표시
        self.status_label = QLabel("카카오톡 창을 검색 중...")
        self.status_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        main_layout.addWidget(self.status_label)

        # 창 선택 영역
        window_frame = self.create_window_selection_frame()
        main_layout.addWidget(window_frame)

        # 대화 내용 영역
        self.chat_text = QTextEdit()
        self.chat_text.setPlaceholderText("1. 카카오톡 창을 선택하세요\n2. '대화 가져오기' 버튼을 클릭하세요\n3. 답변을 생성하고 선택하세요")
        self.chat_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                padding: 8px;
                font-size: 10px;
                line-height: 1.4;
            }
        """)
        main_layout.addWidget(self.chat_text)

        # 버튼 영역
        button_layout = self.create_button_layout()
        main_layout.addLayout(button_layout)

        # 추천 답변 영역
        self.suggestions_frame = self.create_suggestions_frame()
        main_layout.addWidget(self.suggestions_frame)

        self.setLayout(main_layout)

        # 전체 스타일
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 10px;
            }
        """)

    def create_title_frame(self):
        """타이틀 바 생성"""
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #FEE500; border-radius: 10px;")
        title_layout = QHBoxLayout(title_frame)

        title_label = QLabel("카카오톡 답변 도우미")
        title_label.setFont(QFont("맑은 고딕", 10, QFont.Bold))
        title_label.setStyleSheet("color: #3C1E1E; padding: 5px;")

        close_button = QPushButton("×")
        close_button.setFixedSize(25, 25)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #FEE500;
                color: #3C1E1E;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #E6CF00;
            }
        """)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

        return title_frame

    def create_window_selection_frame(self):
        """창 선택 영역"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { 
                background-color: #F8F8F8; 
                border-radius: 5px; 
                padding: 8px; 
            }
        """)
        layout = QVBoxLayout(frame)

        label = QLabel("카카오톡 대화창:")
        label.setFont(QFont("맑은 고딕", 9, QFont.Bold))
        layout.addWidget(label)

        # 창 선택 드롭다운
        self.window_combo = QComboBox()
        self.window_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
                font-size: 10px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.window_combo.currentTextChanged.connect(self.on_window_selected)
        layout.addWidget(self.window_combo)

        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        refresh_btn.clicked.connect(self.scan_kakao_windows)
        layout.addWidget(refresh_btn)

        return frame

    def create_button_layout(self):
        """버튼 레이아웃"""
        layout = QVBoxLayout()

        # 상단 버튼들
        top_layout = QHBoxLayout()

        # 대화 가져오기
        fetch_btn = QPushButton("📋 대화 가져오기")
        fetch_btn.setStyleSheet("""
            QPushButton {
                background-color: #A3E1FF;
                color: #2C5282;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #7DCFFF;
            }
        """)
        fetch_btn.clicked.connect(self.safe_fetch_chat)

        # 자동 모드
        self.auto_btn = QPushButton("🔄 자동 모드")
        self.auto_btn.setCheckable(True)
        self.auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                color: #2D3748;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 10px;
            }
            QPushButton:checked {
                background-color: #68D391;
                color: white;
                font-weight: bold;
            }
        """)
        self.auto_btn.clicked.connect(self.toggle_auto_mode)

        top_layout.addWidget(fetch_btn)
        top_layout.addWidget(self.auto_btn)
        layout.addLayout(top_layout)

        # 답변 생성 버튼
        generate_btn = QPushButton("🤖 답변 추천 받기")
        generate_btn.setFont(QFont("맑은 고딕", 11, QFont.Bold))
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE500;
                color: #3C1E1E;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #E6CF00;
            }
        """)
        generate_btn.clicked.connect(self.generate_suggestions)
        layout.addWidget(generate_btn)

        return layout

    def create_suggestions_frame(self):
        """추천 답변 영역"""
        frame = QFrame()
        frame.setVisible(False)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(frame)

        title = QLabel("💬 추천 답변 (클릭하여 전송)")
        title.setFont(QFont("맑은 고딕", 9, QFont.Bold))
        title.setStyleSheet("color: #2D3748; margin-bottom: 5px;")
        layout.addWidget(title)

        self.suggestion_buttons = []
        colors = ["#E6FFFA", "#FFF5E6", "#F0F9FF"]

        for i in range(3):
            btn = QPushButton(f"답변 {i + 1}")
            btn.setFont(QFont("맑은 고딕", 9))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors[i]};
                    color: #2D3748;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                    padding: 10px;
                    text-align: left;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: #CBD5E0;
                    border-color: #A0AEC0;
                }}
            """)
            btn.clicked.connect(lambda checked, idx=i: self.safe_use_suggestion(idx))
            layout.addWidget(btn)
            self.suggestion_buttons.append(btn)

        return frame

    def scan_kakao_windows(self):
        """안전한 창 스캔"""
        if not self.scan_thread.isRunning():
            self.scan_thread.start()

    def on_windows_found(self, windows):
        """창 발견 시 처리"""
        self.kakao_windows = windows
        self.update_window_combo()

        if windows:
            self.status_label.setText(f"카카오톡 창 {len(windows)}개 발견")
            self.status_label.setStyleSheet("color: #38A169; font-size: 10px; padding: 5px;")
        else:
            self.status_label.setText("카카오톡 창을 찾을 수 없습니다")
            self.status_label.setStyleSheet("color: #E53E3E; font-size: 10px; padding: 5px;")

    def update_window_combo(self):
        """드롭다운 업데이트"""
        current_text = self.window_combo.currentText()
        self.window_combo.clear()

        if not self.kakao_windows:
            self.window_combo.addItem("카카오톡을 실행해주세요")
            return

        for window in self.kakao_windows:
            title = window['title']
            if len(title) > 30:
                title = title[:27] + "..."
            self.window_combo.addItem(title, window)

        # 이전 선택 복원
        if current_text:
            index = self.window_combo.findText(current_text)
            if index >= 0:
                self.window_combo.setCurrentIndex(index)

    def on_window_selected(self):
        """창 선택 처리"""
        data = self.window_combo.currentData()
        if data:
            self.selected_window = data
            print(f"선택된 창: {data['title']}")

    def safe_fetch_chat(self):
        """안전한 대화 가져오기 (자동 클릭 포함)"""
        if not self.selected_window:
            QMessageBox.warning(self, "창 선택 필요", "먼저 카카오톡 대화창을 선택해주세요.")
            return

        hwnd = self.selected_window['hwnd']

        # 창이 여전히 유효한지 확인
        if not win32gui.IsWindow(hwnd):
            QMessageBox.warning(self, "창 오류", "선택한 창이 더 이상 유효하지 않습니다.\n새로고침 후 다시 선택해주세요.")
            return

        try:
            # 클립보드 백업
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass

            # 상태 업데이트
            self.status_label.setText("대화 영역을 찾는 중...")
            self.status_label.setStyleSheet("color: #3182CE; font-size: 10px; padding: 5px;")
            QApplication.processEvents()  # UI 업데이트

            # 1단계: 대화 영역 자동 클릭
            chat_area_found = SafeWindowHandler.find_chat_area_and_click(hwnd)

            if not chat_area_found:
                # 대화 영역을 찾지 못했을 때 기본 위치 클릭
                self.status_label.setText("기본 위치 클릭 시도 중...")
                QApplication.processEvents()
                SafeWindowHandler.click_window_area(hwnd, 0.5, 0.4)
            else:
                self.status_label.setText("대화 영역 발견! 내용 복사 중...")
                QApplication.processEvents()

            time.sleep(0.5)  # 클릭 후 안정화 시간

            # 2단계: 전체 선택 및 복사
            success = False

            # 방법 1: 표준 복사
            if SafeWindowHandler.safe_send_keys("^a", hwnd):
                time.sleep(0.3)
                if SafeWindowHandler.safe_send_keys("^c", hwnd):
                    time.sleep(0.5)

                    try:
                        chat_content = pyperclip.paste()
                        if (chat_content and
                                chat_content != original_clipboard and
                                len(chat_content.strip()) > 10):  # 최소 길이 확인

                            self.chat_text.setPlainText(chat_content)
                            self.status_label.setText(f"성공! {len(chat_content)}자 가져옴")
                            self.status_label.setStyleSheet("color: #38A169; font-size: 10px; padding: 5px;")

                            QMessageBox.information(self, "✅ 성공", f"대화 내용을 자동으로 가져왔습니다!")
                            success = True

                    except Exception as e:
                        print(f"클립보드 읽기 오류: {e}")

            # 방법 2: 다른 위치 시도
            if not success:
                self.status_label.setText("다른 위치에서 재시도 중...")
                QApplication.processEvents()

                # 여러 위치 시도
                positions = [(0.3, 0.3), (0.7, 0.3), (0.5, 0.6)]

                for x, y in positions:
                    SafeWindowHandler.click_window_area(hwnd, x, y)
                    time.sleep(0.3)

                    if SafeWindowHandler.safe_send_keys("^a", hwnd):
                        time.sleep(0.2)
                        if SafeWindowHandler.safe_send_keys("^c", hwnd):
                            time.sleep(0.3)

                            try:
                                content = pyperclip.paste()
                                if (content and
                                        content != original_clipboard and
                                        len(content.strip()) > 10):
                                    self.chat_text.setPlainText(content)
                                    self.status_label.setText(f"성공! {len(content)}자 가져옴")
                                    self.status_label.setStyleSheet("color: #38A169; font-size: 10px; padding: 5px;")

                                    QMessageBox.information(self, "✅ 재시도 성공",
                                                            f"다른 위치에서 대화 내용을 가져왔습니다!\n길이: {len(content)} 문자")
                                    success = True
                                    break
                            except:
                                continue

            if not success:
                self.status_label.setText("대화 내용을 찾을 수 없음")
                self.status_label.setStyleSheet("color: #E53E3E; font-size: 10px; padding: 5px;")

                QMessageBox.information(self, "❓ 수동 조작 필요",
                                        "자동으로 대화 내용을 찾지 못했습니다.\n\n📋 수동 방법:\n1. 카카오톡 대화 영역을 클릭\n2. Ctrl+A로 전체 선택\n3. Ctrl+C로 복사\n4. 이 프로그램으로 돌아와서 Ctrl+V로 붙여넣기")

            # 원래 창으로 복귀
            self.activateWindow()

        except Exception as e:
            self.status_label.setText("오류 발생")
            self.status_label.setStyleSheet("color: #E53E3E; font-size: 10px; padding: 5px;")
            QMessageBox.critical(self, "❌ 오류",
                                 f"대화 가져오기 중 오류 발생:\n\n{str(e)}\n\n🔧 해결 방법:\n- 카카오톡을 다시 실행\n- 프로그램을 관리자 권한으로 실행\n- 새로고침 후 다시 시도")

    def toggle_auto_mode(self):
        """자동 모드 토글"""
        if self.auto_btn.isChecked():
            if not self.selected_window:
                self.auto_btn.setChecked(False)
                QMessageBox.warning(self, "창 선택 필요", "자동 모드를 위해 먼저 카카오톡 창을 선택해주세요.")
                return

            self.clip_timer.start(3000)  # 3초마다 확인
            self.status_label.setText("자동 모드 활성화")
            self.status_label.setStyleSheet("color: #38A169; font-size: 10px; padding: 5px;")
        else:
            self.clip_timer.stop()
            self.status_label.setText("수동 모드")
            self.status_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")

    def check_clipboard(self):
        """클립보드 자동 확인"""
        if not self.auto_btn.isChecked():
            return

        try:
            current = pyperclip.paste()
            if (current and current != self.last_clipboard and
                    len(current.strip()) > 10):
                self.last_clipboard = current
                self.chat_text.setPlainText(current)
        except Exception as e:
            print(f"클립보드 확인 오류: {e}")

    def generate_suggestions(self):
        """답변 생성"""
        content = self.chat_text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "내용 없음", "먼저 대화 내용을 입력하거나 가져와주세요.")
            return

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 카카오톡 대화에 대한 자연스럽고 적절한 답변을 추천해주는 도우미입니다. 다음 조건을 만족하는 답변 3개를 생성해주세요:\n1. 각각 다른 톤(정중함, 친근함, 재미있음)\n2. 간결하고 자연스러운 한국어\n3. 상황에 맞는 적절한 반응"
                    },
                    {
                        "role": "user",
                        "content": f"다음 카카오톡 대화에 대한 적절한 답변을 추천해주세요:\n\n{content}"
                    }
                ],
                n=3,
                temperature=0.8,
                max_tokens=80
            )

            suggestions = [choice.message.content.strip() for choice in response.choices]
            self.display_suggestions(suggestions)

        except Exception as e:
            QMessageBox.critical(self, "API 오류", f"답변 생성 실패:\n{str(e)}")

    def display_suggestions(self, suggestions):
        """답변 표시"""
        self.suggestions_frame.setVisible(True)

        for i, suggestion in enumerate(suggestions):
            if i < len(self.suggestion_buttons):
                display_text = suggestion[:60] + "..." if len(suggestion) > 60 else suggestion
                self.suggestion_buttons[i].setText(display_text)
                self.suggestion_buttons[i].setToolTip(suggestion)
                self.suggestion_buttons[i].setProperty("full_text", suggestion)

    def safe_use_suggestion(self, index):
        """안전한 답변 사용"""
        if index >= len(self.suggestion_buttons):
            return

        full_text = self.suggestion_buttons[index].property("full_text")
        if not full_text:
            return

        # 클립보드에 복사
        try:
            pyperclip.copy(full_text)
        except Exception as e:
            QMessageBox.warning(self, "복사 실패", f"클립보드 복사 실패: {str(e)}")
            return

        if not self.selected_window:
            QMessageBox.information(self, "복사 완료", "답변이 클립보드에 복사되었습니다.")
            return

        hwnd = self.selected_window['hwnd']

        # 창 유효성 확인
        if not win32gui.IsWindow(hwnd):
            QMessageBox.warning(self, "창 오류", "선택한 창이 더 이상 유효하지 않습니다.")
            return

        try:
            # 안전한 붙여넣기
            if SafeWindowHandler.safe_send_keys("^v", hwnd):
                QMessageBox.information(self, "전송 완료", "답변이 카카오톡에 입력되었습니다!")
            else:
                QMessageBox.warning(self, "입력 실패", "자동 입력에 실패했습니다.\n수동으로 붙여넣어주세요.")

        except Exception as e:
            QMessageBox.warning(self, "전송 실패", f"답변 전송 실패:\n{str(e)}")

    # 마우스 이벤트 (드래그)
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

    def closeEvent(self, event):
        """프로그램 종료 시 정리"""
        try:
            if hasattr(self, 'scan_timer'):
                self.scan_timer.stop()
            if hasattr(self, 'clip_timer'):
                self.clip_timer.stop()
            if hasattr(self, 'scan_thread') and self.scan_thread.isRunning():
                self.scan_thread.quit()
                self.scan_thread.wait()
        except:
            pass
        event.accept()


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont("맑은 고딕", 9))

        window = StableKakaoTalkAssistant()
        window.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"프로그램 시작 오류: {e}")
        traceback.print_exc()