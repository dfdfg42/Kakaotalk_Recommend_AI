# main.py - 메인 애플리케이션

import sys
import time
import traceback
import pyperclip
import openai
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QFont
import win32gui
from openai import OpenAI

# 로컬 모듈들
from config import *
from window_handler import SafeWindowHandler
from window_scanner import WindowManager
from ui_components import UIComponents


class KakaoTalkAssistant(QWidget):
    """카카오톡 답변 추천 메인 애플리케이션"""

    def __init__(self):
        super().__init__()

        # OpenAI API 키 설정
        client = OpenAI(api_key=OPENAI_API_KEY)


        # 윈도우 설정
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 창 크기 및 위치
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.position_window()

        # 변수 초기화
        self.window_manager = WindowManager()
        self.old_pos = None
        self.dragging = False
        self.last_clipboard = ""

        # UI 초기화
        self.init_ui()

        # 타이머 설정
        self.setup_timers()

        # 윈도우 스캔 시작
        self.start_window_scanning()

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
        self.scan_timer.start(WINDOW_SCAN_INTERVAL)

        # 클립보드 확인 타이머
        self.clip_timer = QTimer(self)
        self.clip_timer.timeout.connect(self.check_clipboard)

    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 타이틀 바
        title_frame, close_button = UIComponents.create_title_frame()
        close_button.clicked.connect(self.close)
        main_layout.addWidget(title_frame)

        # 상태 표시
        self.status_label = UIComponents.create_status_label()
        main_layout.addWidget(self.status_label)

        # 창 선택 영역
        window_frame, self.window_combo, refresh_btn = UIComponents.create_window_selection_frame()
        self.window_combo.currentTextChanged.connect(self.on_window_selected)
        refresh_btn.clicked.connect(self.scan_kakao_windows)
        main_layout.addWidget(window_frame)

        # 대화 내용 영역
        self.chat_text = UIComponents.create_chat_text_area()
        main_layout.addWidget(self.chat_text)

        # 버튼 영역
        button_layout, fetch_btn, self.auto_btn, generate_btn = UIComponents.create_button_layout()
        fetch_btn.clicked.connect(self.safe_fetch_chat)
        self.auto_btn.clicked.connect(self.toggle_auto_mode)
        generate_btn.clicked.connect(self.generate_suggestions)
        main_layout.addLayout(button_layout)

        # 추천 답변 영역
        self.suggestions_frame, self.suggestion_buttons = UIComponents.create_suggestions_frame()
        for i, btn in enumerate(self.suggestion_buttons):
            btn.clicked.connect(lambda checked, idx=i: self.safe_use_suggestion(idx))
        main_layout.addWidget(self.suggestions_frame)

        self.setLayout(main_layout)
        UIComponents.set_main_window_style(self)

    def start_window_scanning(self):
        """윈도우 스캔 시작"""
        self.window_manager.start_scanning(self.on_windows_found)
        self.scan_kakao_windows()

    def scan_kakao_windows(self):
        """카카오톡 창 스캔"""
        if not self.window_manager.scan_thread.isRunning():
            self.window_manager.scan_thread.start()

    def on_windows_found(self, windows):
        """창 발견 시 처리"""
        self.window_manager.update_windows(windows)
        self.update_window_combo()

        if windows:
            UIComponents.update_status_label(
                self.status_label,
                f"카카오톡 창 {len(windows)}개 발견",
                "success"
            )
        else:
            UIComponents.update_status_label(
                self.status_label,
                "카카오톡 창을 찾을 수 없습니다",
                "error"
            )

    def update_window_combo(self):
        """드롭다운 업데이트"""
        current_text = self.window_combo.currentText()
        self.window_combo.clear()

        windows = self.window_manager.get_window_list()
        if not windows:
            self.window_combo.addItem("카카오톡을 실행해주세요")
            return

        for window in windows:
            title = self.window_manager.format_window_title(window['title'])
            self.window_combo.addItem(title, window)

        # 이전 선택 복원
        if current_text:
            index = self.window_combo.findText(current_text)
            if index >= 0:
                self.window_combo.setCurrentIndex(index)

    def on_window_selected(self):
        """창 선택 처리"""
        data = self.window_combo.currentData()
        self.window_manager.select_window(data)

    def safe_fetch_chat(self):
        """안전한 대화 가져오기 (자동 클릭 포함)"""
        hwnd = self.window_manager.get_selected_hwnd()
        if not hwnd:
            QMessageBox.warning(self, "창 선택 필요", "먼저 카카오톡 대화창을 선택해주세요.")
            return

        if not self.window_manager.is_selected_window_valid():
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
            UIComponents.update_status_label(self.status_label, "대화 영역을 찾는 중...", "info")
            QApplication.processEvents()

            # 1단계: 대화 영역 자동 클릭
            chat_area_found = SafeWindowHandler.find_chat_area_and_click(hwnd)

            if not chat_area_found:
                UIComponents.update_status_label(self.status_label, "기본 위치 클릭 시도 중...", "info")
                QApplication.processEvents()
                SafeWindowHandler.click_window_area(hwnd, 0.5, 0.4)
            else:
                UIComponents.update_status_label(self.status_label, "대화 영역 발견! 내용 복사 중...", "info")
                QApplication.processEvents()

            time.sleep(DELAYS['copy_wait'])

            # 2단계: 전체 선택 및 복사
            success = self._try_copy_chat_content(hwnd, original_clipboard)

            if not success:
                success = self._retry_copy_at_different_positions(hwnd, original_clipboard)

            if not success:
                UIComponents.update_status_label(self.status_label, "대화 내용을 찾을 수 없음", "error")
                QMessageBox.information(self, "❓ 수동 조작 필요",
                                        "자동으로 대화 내용을 찾지 못했습니다.\n\n📋 수동 방법:\n1. 카카오톡 대화 영역을 클릭\n2. Ctrl+A로 전체 선택\n3. Ctrl+C로 복사\n4. 이 프로그램으로 돌아와서 Ctrl+V로 붙여넣기")

            # 원래 창으로 복귀
            self.activateWindow()

        except Exception as e:
            UIComponents.update_status_label(self.status_label, "오류 발생", "error")
            QMessageBox.critical(self, "❌ 오류",
                                 f"대화 가져오기 중 오류 발생:\n\n{str(e)}\n\n🔧 해결 방법:\n- 카카오톡을 다시 실행\n- 프로그램을 관리자 권한으로 실행\n- 새로고침 후 다시 시도")

    def _try_copy_chat_content(self, hwnd, original_clipboard):
        """대화 내용 복사 시도"""
        if SafeWindowHandler.safe_send_keys("^a", hwnd):
            time.sleep(DELAYS['focus_wait'])
            if SafeWindowHandler.safe_send_keys("^c", hwnd):
                time.sleep(DELAYS['copy_wait'])

                try:
                    chat_content = pyperclip.paste()
                    if (chat_content and
                            chat_content != original_clipboard and
                            len(chat_content.strip()) > MIN_CHAT_LENGTH):
                        self.chat_text.setPlainText(chat_content)
                        UIComponents.update_status_label(
                            self.status_label,
                            f"성공! {len(chat_content)}자 가져옴",
                            "success"
                        )

                        first_line = chat_content.split('\n')[0][:50] if chat_content.split('\n') else '(내용 없음)'
                        QMessageBox.information(self, "✅ 성공",
                                                f"대화 내용을 자동으로 가져왔습니다!\n\n📊 길이: {len(chat_content)} 문자\n💬 첫 줄: {first_line}")
                        return True

                except Exception as e:
                    print(f"클립보드 읽기 오류: {e}")
        return False

    def _retry_copy_at_different_positions(self, hwnd, original_clipboard):
        """다른 위치에서 복사 재시도"""
        UIComponents.update_status_label(self.status_label, "다른 위치에서 재시도 중...", "info")
        QApplication.processEvents()

        for x, y in RETRY_POSITIONS:
            SafeWindowHandler.click_window_area(hwnd, x, y)
            time.sleep(DELAYS['focus_wait'])

            if SafeWindowHandler.safe_send_keys("^a", hwnd):
                time.sleep(DELAYS['click_stabilize'])
                if SafeWindowHandler.safe_send_keys("^c", hwnd):
                    time.sleep(DELAYS['focus_wait'])

                    try:
                        content = pyperclip.paste()
                        if (content and
                                content != original_clipboard and
                                len(content.strip()) > MIN_CHAT_LENGTH):
                            self.chat_text.setPlainText(content)
                            UIComponents.update_status_label(
                                self.status_label,
                                f"성공! {len(content)}자 가져옴",
                                "success"
                            )

                            QMessageBox.information(self, "✅ 재시도 성공",
                                                    f"다른 위치에서 대화 내용을 가져왔습니다!\n길이: {len(content)} 문자")
                            return True
                    except:
                        continue
        return False

    def toggle_auto_mode(self):
        """자동 모드 토글"""
        if self.auto_btn.isChecked():
            if not self.window_manager.get_selected_hwnd():
                self.auto_btn.setChecked(False)
                QMessageBox.warning(self, "창 선택 필요", "자동 모드를 위해 먼저 카카오톡 창을 선택해주세요.")
                return

            self.clip_timer.start(CLIPBOARD_CHECK_INTERVAL)
            UIComponents.update_status_label(self.status_label, "자동 모드 활성화", "success")
        else:
            self.clip_timer.stop()
            UIComponents.update_status_label(self.status_label, "수동 모드", "info")

    def check_clipboard(self):
        """클립보드 자동 확인"""
        if not self.auto_btn.isChecked():
            return

        try:
            current = pyperclip.paste()
            if (current and current != self.last_clipboard and
                    len(current.strip()) > MIN_CHAT_LENGTH):
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
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"다음 카카오톡 대화에 대한 적절한 답변을 추천해주세요:\n\n{content}"}
                ],
                n=GPT_N_SUGGESTIONS,
                temperature=GPT_TEMPERATURE,
                max_tokens=GPT_MAX_TOKENS
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
        """안전한 답변 사용 (입력창 자동 탐지 + 전송)"""
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

        hwnd = self.window_manager.get_selected_hwnd()
        if not hwnd:
            QMessageBox.information(self, "복사 완료", "답변이 클립보드에 복사되었습니다.")
            return

        if not self.window_manager.is_selected_window_valid():
            QMessageBox.warning(self, "창 오류", "선택한 창이 더 이상 유효하지 않습니다.")
            return

        try:
            # 입력창 찾기 및 메시지 입력
            success = self._input_message_to_kakao(hwnd, full_text)

            if success:
                # 전송 확인
                self._handle_message_sending(hwnd, full_text)
            else:
                UIComponents.update_status_label(self.status_label, "❌ 입력 실패", "error")
                QMessageBox.warning(self, "입력 실패", "메시지 입력에 실패했습니다.\n수동으로 붙여넣어주세요.")

        except Exception as e:
            UIComponents.update_status_label(self.status_label, "❌ 오류 발생", "error")
            QMessageBox.warning(self, "전송 실패",
                                f"답변 전송 실패:\n\n{str(e)}\n\n🔧 해결책:\n- 카카오톡 창을 활성화\n- 입력창을 직접 클릭\n- Ctrl+V로 수동 붙여넣기")

    def _input_message_to_kakao(self, hwnd, full_text):
        """카카오톡에 메시지 입력"""
        UIComponents.update_status_label(self.status_label, "입력창을 찾는 중...", "info")
        QApplication.processEvents()

        # 입력창 찾아서 클릭
        input_found = SafeWindowHandler.find_input_area_and_click(hwnd)

        if input_found:
            UIComponents.update_status_label(self.status_label, "입력창 발견! 메시지 입력 중...", "info")
        else:
            UIComponents.update_status_label(self.status_label, "기본 입력창 위치 시도 중...", "info")
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.85)

        QApplication.processEvents()
        time.sleep(DELAYS['copy_wait'])

        # 메시지 입력 시도
        if SafeWindowHandler.safe_send_keys("^v", hwnd):
            time.sleep(DELAYS['paste_wait'])
            UIComponents.update_status_label(self.status_label, "메시지 입력 완료!", "success")
            return True
        else:
            # 직접 타이핑 시도
            UIComponents.update_status_label(self.status_label, "직접 입력 방식으로 재시도...", "info")
            QApplication.processEvents()

            SafeWindowHandler.safe_send_keys("^a")
            time.sleep(0.1)

            for char in full_text:
                SafeWindowHandler.send_char(char)
                time.sleep(0.02)

            UIComponents.update_status_label(self.status_label, "직접 입력 완료!", "success")
            return True

    def _handle_message_sending(self, hwnd, full_text):
        """메시지 전송 처리"""
        reply = QMessageBox.question(
            self,
            "🚀 전송 확인",
            f"다음 메시지를 전송하시겠습니까?\n\n💬 \"{full_text[:100]}{'...' if len(full_text) > 100 else ''}\"\n\n✅ 확인을 누르면 자동으로 전송됩니다.\n❌ 취소를 누르면 입력만 하고 전송하지 않습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            UIComponents.update_status_label(self.status_label, "카카오톡으로 포커스 이동 중...", "info")
            QApplication.processEvents()

            try:
                # 카카오톡 창으로 다시 포커스 이동
                SafeWindowHandler.focus_window(hwnd)
                SafeWindowHandler.click_window_area(hwnd, 0.5, 0.85)
                time.sleep(DELAYS['focus_wait'])

                UIComponents.update_status_label(self.status_label, "전송 중...", "info")
                QApplication.processEvents()

                # 엔터 키로 전송
                if SafeWindowHandler.send_enter():
                    time.sleep(DELAYS['send_wait'])

                    UIComponents.update_status_label(self.status_label, "✅ 메시지 전송 완료!", "success")

                    # 전송 성공 알림 (지연)
                    QTimer.singleShot(100, lambda: QMessageBox.information(
                        self,
                        "🎉 전송 성공!",
                        f"메시지가 성공적으로 전송되었습니다!\n\n📤 전송된 내용:\n\"{full_text[:150]}{'...' if len(full_text) > 150 else ''}\""
                    ))

                    # 추천 답변 숨기기
                    self.suggestions_frame.setVisible(False)

                else:
                    UIComponents.update_status_label(self.status_label, "⚠️ 전송 실패 - 수동으로 엔터 눌러주세요", "warning")

            except Exception as e:
                UIComponents.update_status_label(self.status_label, "⚠️ 포커스 이동 실패", "error")
                QMessageBox.warning(self, "전송 실패", f"카카오톡 포커스 이동 실패:\n{str(e)}\n\n💡 해결책: 카카오톡 창을 클릭하고 수동으로 엔터를 눌러주세요.")
        else:
            UIComponents.update_status_label(self.status_label, "✏️ 입력 완료 (전송 안함)", "info")
            QMessageBox.information(self, "입력 완료", "메시지가 입력되었습니다.\n원하실 때 엔터를 눌러 전송하세요.")

    # 마우스 이벤트 (드래그 기능)
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
            self.window_manager.stop_scanning()
        except:
            pass
        event.accept()


def main():
    """메인 실행 함수"""
    try:
        app = QApplication(sys.argv)
        app.setFont(QFont("맑은 고딕", 9))

        window = KakaoTalkAssistant()
        window.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"프로그램 시작 오류: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()