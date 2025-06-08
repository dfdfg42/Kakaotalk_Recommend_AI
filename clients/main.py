# main.py - 메인 애플리케이션 (파서 선택 기능 추가)

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

# 파서 선택에 따른 import
if PARSER_TYPE == "date":
    from chat_date_parser import KakaoTalkDateParser as ChatParser

    PARSER_NAME = "날짜 기반 파서"
    PARSER_DESCRIPTION = f"최근 {DATE_LIMIT_HOURS}시간"
else:  # PARSER_TYPE == "count" (기본값)
    from chat_parser import KakaoTalkChatParser as ChatParser

    PARSER_NAME = "개수 기반 파서"
    PARSER_DESCRIPTION = f"최근 {MAX_RECENT_MESSAGES}개 메시지"

# OpenAI API 키 설정
client = OpenAI(api_key=OPENAI_API_KEY)


class KakaoTalkAssistant(QWidget):
    """카카오톡 답변 추천 메인 애플리케이션"""

    def __init__(self):
        super().__init__()

        # 윈도우 설정
        window_title = WINDOW_TITLE

        # 파서 정보를 타이틀에 추가
        if PARSER_TYPE == "date":
            window_title += f" - 날짜 모드 ({DATE_LIMIT_HOURS}시간)"
        else:
            window_title += f" - 개수 모드 ({MAX_RECENT_MESSAGES}개)"

        if USE_FINE_TUNED_MODEL and FINE_TUNED_MODEL_ID:
            window_title += " - 고경우 모드"

        self.setWindowTitle(window_title)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 창 크기 및 위치
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.position_window()

        # 변수 초기화
        self.window_manager = WindowManager()
        self.chat_parser = ChatParser()  # 선택된 파서 사용
        self.old_pos = None
        self.dragging = False
        self.last_clipboard = ""

        # 파서 정보 출력
        print(f"🔧 {PARSER_NAME} 활성화 - {PARSER_DESCRIPTION}")

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
                f"카카오톡 창 {len(windows)}개 발견 ({PARSER_NAME})",
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
        """안전한 대화 가져오기 (선택된 파서 사용)"""
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
        """대화 내용 복사 시도 (선택된 파서로 처리)"""
        if SafeWindowHandler.safe_send_keys("^a", hwnd):
            time.sleep(DELAYS['focus_wait'])
            if SafeWindowHandler.safe_send_keys("^c", hwnd):
                time.sleep(DELAYS['copy_wait'])

                try:
                    chat_content = pyperclip.paste()
                    if (chat_content and
                            chat_content != original_clipboard and
                            len(chat_content.strip()) > MIN_CHAT_LENGTH):

                        # 선택된 파서로 대화 분석
                        UIComponents.update_status_label(self.status_label, f"{PARSER_NAME} 분석 중...", "info")
                        QApplication.processEvents()

                        # 파서 타입에 따라 다른 메서드 호출
                        if PARSER_TYPE == "date":
                            messages = self.chat_parser.extract_last_day_messages(chat_content)
                        else:  # count
                            messages = self.chat_parser.extract_recent_messages(chat_content, MAX_RECENT_MESSAGES)

                        if messages:
                            # GPT 전송용 포맷으로 변환
                            formatted_chat = self.chat_parser.format_messages_for_gpt(messages)

                            # 대화 요약 정보 생성
                            summary = self.chat_parser.get_chat_summary(messages)

                            # UI에 표시
                            self.chat_text.setPlainText(formatted_chat)

                            # 파서별 상태 메시지
                            if PARSER_TYPE == "date":
                                status_msg = f"성공! {summary['total_messages']}개 메시지 (최근 {DATE_LIMIT_HOURS}시간), {len(summary['participants'])}명 참여"
                            else:
                                status_msg = f"성공! {summary['total_messages']}개 메시지 (최근 {MAX_RECENT_MESSAGES}개 중), {len(summary['participants'])}명 참여"

                            UIComponents.update_status_label(self.status_label, status_msg, "success")

                            # 성공 메시지에 요약 정보 포함
                            participant_names = ', '.join(summary['participants'][:3])  # 최대 3명만 표시
                            if len(summary['participants']) > 3:
                                participant_names += f" 외 {len(summary['participants']) - 3}명"

                            # 파서별 성공 메시지
                            if PARSER_TYPE == "date":
                                success_title = "✅ 날짜 기반 대화 추출 성공"
                                time_info = f"🕒 시간 범위: {summary.get('time_range', '정보 없음')}"
                            else:
                                success_title = "✅ 개수 기반 대화 추출 성공"
                                time_info = f"📊 최근 {MAX_RECENT_MESSAGES}개 중 {summary['total_messages']}개 추출"

                            QMessageBox.information(self, success_title,
                                                    f"{PARSER_DESCRIPTION} 범위에서 {summary['total_messages']}개 메시지를 분석했습니다!\n\n"
                                                    f"👥 참여자: {participant_names}\n"
                                                    f"📝 마지막 발신자: {summary['last_sender']}\n"
                                                    f"{time_info}\n"
                                                    f"🗑️ 시스템 메시지 제거됨\n\n"
                                                    f"💬 미리보기:\n{summary['preview'][:100]}{'...' if len(summary['preview']) > 100 else ''}")
                            return True
                        else:
                            # 파싱된 메시지가 없으면 원본 사용
                            self.chat_text.setPlainText(chat_content)
                            UIComponents.update_status_label(
                                self.status_label,
                                f"성공! {len(chat_content)}자 가져옴 (분석 불가)",
                                "warning"
                            )
                            QMessageBox.information(self, "⚠️ 원본 텍스트 사용",
                                                    f"대화 내용을 가져왔지만 {PARSER_NAME} 분석에 실패했습니다.\n원본 텍스트를 사용합니다.\n\n📊 길이: {len(chat_content)} 문자")
                            return True

                except Exception as e:
                    print(f"클립보드 읽기 또는 파싱 오류: {e}")
        return False

    def _retry_copy_at_different_positions(self, hwnd, original_clipboard):
        """다른 위치에서 복사 재시도 (선택된 파서 사용)"""
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

                            # 재시도에서도 선택된 파서 사용
                            print(f"\n📋 재시도 {PARSER_NAME} 분석 시작")

                            if PARSER_TYPE == "date":
                                messages = self.chat_parser.extract_last_day_messages(content)
                            else:
                                messages = self.chat_parser.extract_recent_messages(content, MAX_RECENT_MESSAGES)

                            print(f"📊 재시도 분석 완료 - 추출된 메시지: {len(messages)}개\n")

                            if messages:
                                # GPT 전송용 포맷으로 변환
                                formatted_chat = self.chat_parser.format_messages_for_gpt(messages)
                                summary = self.chat_parser.get_chat_summary(messages)

                                self.chat_text.setPlainText(formatted_chat)
                                UIComponents.update_status_label(
                                    self.status_label,
                                    f"✅ 재시도 성공: {summary['total_messages']}개 메시지 ({PARSER_NAME})",
                                    "success"
                                )

                                QMessageBox.information(self, "✅ 재시도 성공",
                                                        f"다른 위치에서 {PARSER_DESCRIPTION} 범위의 {summary['total_messages']}개 메시지를 추출했습니다!\n\n"
                                                        f"👥 참여자: {', '.join(summary['participants'][:3])}")
                                return True
                            else:
                                # 파싱 실패시 원본 사용
                                self.chat_text.setPlainText(content)
                                UIComponents.update_status_label(
                                    self.status_label,
                                    f"재시도 성공: {len(content)}자 (분석 불가)",
                                    "warning"
                                )
                                QMessageBox.information(self, "⚠️ 재시도 성공 (원본)",
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
            UIComponents.update_status_label(self.status_label, f"자동 모드 활성화 ({PARSER_DESCRIPTION})", "success")
        else:
            self.clip_timer.stop()
            UIComponents.update_status_label(self.status_label, "수동 모드", "info")

    def check_clipboard(self):
        """클립보드 자동 확인 (선택된 파서 사용)"""
        if not self.auto_btn.isChecked():
            return

        try:
            current = pyperclip.paste()
            if (current and current != self.last_clipboard and
                    len(current.strip()) > MIN_CHAT_LENGTH):
                self.last_clipboard = current

                # 자동 모드에서도 선택된 파서 사용
                print(f"\n🔄 자동 모드 - {PARSER_NAME} 분석 시작")

                if PARSER_TYPE == "date":
                    messages = self.chat_parser.extract_last_day_messages(current)
                else:
                    messages = self.chat_parser.extract_recent_messages(current, MAX_RECENT_MESSAGES)

                print(f"📊 자동 분석 완료 - 추출된 메시지: {len(messages)}개\n")

                if messages:
                    formatted_chat = self.chat_parser.format_messages_for_gpt(messages)
                    self.chat_text.setPlainText(formatted_chat)

                    summary = self.chat_parser.get_chat_summary(messages)
                    UIComponents.update_status_label(
                        self.status_label,
                        f"🔄 자동 감지: {summary['total_messages']}개 메시지 ({PARSER_NAME})",
                        "success"
                    )
                else:
                    # 파싱 실패시 원본 사용
                    self.chat_text.setPlainText(current)
                    UIComponents.update_status_label(
                        self.status_label,
                        f"🔄 자동 감지: {len(current)}자 (분석 불가)",
                        "warning"
                    )

        except Exception as e:
            print(f"클립보드 확인 오류: {e}")

    def generate_suggestions(self):
        """답변 생성 (긍정/중립/부정 3가지 확실 구분)"""
        content = self.chat_text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "내용 없음", "먼저 대화 내용을 입력하거나 가져와주세요.")
            return

        try:
            UIComponents.update_status_label(self.status_label, "🤖 AI가 답변을 생성 중...", "info")
            QApplication.processEvents()

            # 모델 선택
            if USE_FINE_TUNED_MODEL and FINE_TUNED_MODEL_ID:
                model = FINE_TUNED_MODEL_ID
                base_prompt = KOKYUNGWOO_PROMPT
                UIComponents.update_status_label(self.status_label, "🤖 고경우 AI가 답변 생성 중...", "info")
            else:
                model = GPT_MODEL
                base_prompt = SYSTEM_PROMPT
                UIComponents.update_status_label(self.status_label, "🤖 기본 AI가 답변 생성 중...", "info")

            QApplication.processEvents()

            # ===== 🎯 3개의 개별 프롬프트로 3번 API 호출 =====
            suggestions = []

            # 1. 긍정적 답변 생성
            UIComponents.update_status_label(self.status_label, "😊 긍정적 답변 생성 중...", "info")
            QApplication.processEvents()
            positive_response = self._generate_single_response(model, base_prompt, content, "긍정적")
            suggestions.append(positive_response)

            # 2. 중립적 답변 생성
            UIComponents.update_status_label(self.status_label, "😐 중립적 답변 생성 중...", "info")
            QApplication.processEvents()
            neutral_response = self._generate_single_response(model, base_prompt, content, "중립적")
            suggestions.append(neutral_response)

            # 3. 부정적 답변 생성
            UIComponents.update_status_label(self.status_label, "😔 부정적 답변 생성 중...", "info")
            QApplication.processEvents()
            negative_response = self._generate_single_response(model, base_prompt, content, "부정적")
            suggestions.append(negative_response)

            # UI에 표시
            self.display_suggestions(suggestions)

            # 성공 메시지
            model_info = "고경우 모델" if USE_FINE_TUNED_MODEL and FINE_TUNED_MODEL_ID else "기본 모델"
            UIComponents.update_status_label(self.status_label, f"✅ {model_info} 긍정/중립/부정 답변 완료!", "success")

        except Exception as e:
            UIComponents.update_status_label(self.status_label, "❌ API 오류", "error")
            error_msg = str(e)
            if "does not exist" in error_msg and FINE_TUNED_MODEL_ID:
                QMessageBox.critical(self, "모델 오류",
                                     f"파인튜닝된 모델을 찾을 수 없습니다:\n{FINE_TUNED_MODEL_ID}\n\n기본 모델을 사용하려면 config.py에서 USE_FINE_TUNED_MODEL을 False로 설정하세요.")
            else:
                QMessageBox.critical(self, "API 오류", f"답변 생성 실패:\n{error_msg}")

    def _generate_single_response(self, model, base_prompt, content, tone_type):
        """개별 톤의 답변 하나 생성"""
        try:
            if USE_FINE_TUNED_MODEL and FINE_TUNED_MODEL_ID:
                # 파인튜닝된 모델용 - 각 톤별 구체적 지시
                tone_instructions = {
                    "긍정적": """
    🎯 긍정적이고 밝은 고경우 답변을 해주세요:
    - 밝고 적극적인 반응
    - ㅋㅋ, ㅇㅇ 같은 긍정적 감정표현 사용
    - "좋아", "ㄱㄱ", "오케이" 등의 긍정어 활용
    - 예: "ㅇㅇ 좋지 ㅋㅋ", "ㄱㄱ해보자", "오케이~"
                    """,
                    "중립적": """
    🎯 중립적이고 무난한 고경우 답변을 해주세요:
    - 균형잡힌 무난한 반응
    - 강한 감정 없이 담담하게
                    """,
                    "부정적": """
    🎯 부정적이고 소극적인 고경우 답변을 해주세요:
    - 조심스럽거나 소극적인 반응
    - "싫어", "ㄴㄴ", "망했다" 등의 부정어 활용

                    """
                }

                specific_instruction = tone_instructions[tone_type]
                messages = [
                    {"role": "user", "content": f"{base_prompt}\n\n{specific_instruction}\n\n대화 내용:\n{content}"}]
            else:
                # 기본 모델용 - 시스템 메시지 활용
                tone_instructions = {
                    "긍정적": "밝고 적극적이며 긍정적인 톤으로 답변해주세요. 상황을 낙관적으로 보고 활발한 반응을 보이세요.",
                    "중립적": "균형잡히고 무난한 톤으로 답변해주세요. 과도한 감정 표현 없이 객관적이고 차분하게 반응하세요.",
                    "부정적": "조심스럽고 소극적인 톤으로 답변해주세요. 상황에 대해 걱정스럽거나 부정적인 시각으로 반응하세요."
                }

                system_message = f"{base_prompt} {tone_instructions[tone_type]}"
                parser_context = f"다음은 {PARSER_DESCRIPTION} 범위의 카카오톡 대화입니다"
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"{parser_context}:\n\n{content}"}
                ]

            # API 호출 (1개만 생성)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                n=1,  # 각 톤당 1개씩만 생성
                temperature=GPT_TEMPERATURE,
                max_tokens=GPT_MAX_TOKENS
            )

            # 응답 정리
            suggestion = response.choices[0].message.content.strip()

            # 후처리 (설명 텍스트 제거)
            import re
            suggestion = re.sub(r'^(긍정적인|부정적인|중립적인).*?답변[:\s]*', '', suggestion, flags=re.IGNORECASE)
            suggestion = re.sub(r'^[0-9]+\.\s*', '', suggestion)
            if ':' in suggestion:
                suggestion = suggestion.split(':', 1)[1].strip()

            first_line = suggestion.split('\n')[0].strip()
            return first_line if first_line else "음..."

        except Exception as e:
            print(f"{tone_type} 답변 생성 오류: {e}")
            return "음..."  # 실패시 기본 답변

    def display_suggestions(self, suggestions):
        """답변 표시 - 긍정/중립/부정 순서 보장"""
        self.suggestions_frame.setVisible(True)

        labels = ["😊 긍정", "😐 중립", "😔 부정"]

        for i, suggestion in enumerate(suggestions):
            if i < len(self.suggestion_buttons):
                # 라벨 + 실제 답변 내용
                display_text = f"{labels[i]}: {suggestion}"
                if len(display_text) > 60:
                    display_text = display_text[:57] + "..."

                self.suggestion_buttons[i].setText(display_text)
                self.suggestion_buttons[i].setToolTip(f"{labels[i]} 답변: {suggestion}")
                self.suggestion_buttons[i].setProperty("full_text", suggestion)  # 전송용은 순수 답변만

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
        UIComponents.update_status_label(self.status_label, "📝 입력창을 찾는 중...", "info")
        QApplication.processEvents()

        # 입력창 찾아서 클릭
        input_found = SafeWindowHandler.find_input_area_and_click(hwnd)

        if input_found:
            UIComponents.update_status_label(self.status_label, "✅ 입력창 발견! 메시지 입력 중...", "info")
        else:
            UIComponents.update_status_label(self.status_label, "⚠️ 기본 입력창 위치 시도 중...", "info")
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.85)

        QApplication.processEvents()
        time.sleep(DELAYS['copy_wait'])

        # 메시지 입력 시도
        if SafeWindowHandler.safe_send_keys("^v", hwnd):
            time.sleep(DELAYS['paste_wait'])
            UIComponents.update_status_label(self.status_label, "✅ 메시지 입력 완료!", "success")
            return True
        else:
            # 직접 타이핑 시도
            UIComponents.update_status_label(self.status_label, "🔄 직접 입력 방식으로 재시도...", "info")
            QApplication.processEvents()

            SafeWindowHandler.safe_send_keys("^a")
            time.sleep(0.1)

            for char in full_text:
                SafeWindowHandler.send_char(char)
                time.sleep(0.02)

            UIComponents.update_status_label(self.status_label, "✅ 직접 입력 완료!", "success")
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
            UIComponents.update_status_label(self.status_label, "🎯 카카오톡으로 포커스 이동 중...", "info")
            QApplication.processEvents()

            try:
                # 카카오톡 창으로 다시 포커스 이동
                SafeWindowHandler.focus_window(hwnd)
                SafeWindowHandler.click_window_area(hwnd, 0.5, 0.85)
                time.sleep(DELAYS['focus_wait'])

                UIComponents.update_status_label(self.status_label, "🚀 전송 중...", "info")
                QApplication.processEvents()

                # 엔터 키로 전송
                if SafeWindowHandler.send_enter():
                    time.sleep(DELAYS['send_wait'])

                    UIComponents.update_status_label(self.status_label, "🎉 메시지 전송 완료!", "success")

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