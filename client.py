# window_handler.py - 최근 20개 대화만 불러오도록 개선된 버전

import ctypes
import time
import win32gui
import win32process
import os
from ctypes import wintypes
from clients.config import DELAYS, CHAT_AREA_POSITIONS, INPUT_AREA_POSITIONS


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
            time.sleep(DELAYS['focus_wait'])

            # 마우스 클릭
            ctypes.windll.user32.SetCursorPos(click_x, click_y)
            time.sleep(0.1)

            # 마우스 왼쪽 버튼 클릭
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP

            time.sleep(DELAYS['click_stabilize'])
            return True

        except Exception as e:
            print(f"윈도우 클릭 실패: {e}")
            return False

    @staticmethod
    def scroll_to_recent_messages(hwnd):
        """최근 메시지로 스크롤 (맨 아래로)"""
        try:
            # 창에 포커스
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(DELAYS['focus_wait'])

            # 대화 영역 클릭
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.6)
            time.sleep(DELAYS['click_stabilize'])

            # Ctrl+End로 맨 아래로 이동
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            ctypes.windll.user32.keybd_event(0x23, 0, 0, 0)  # End down
            ctypes.windll.user32.keybd_event(0x23, 0, 2, 0)  # End up
            ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up

            time.sleep(DELAYS['focus_wait'])
            return True

        except Exception as e:
            print(f"스크롤 실패: {e}")
            return False

    @staticmethod
    def select_recent_messages(hwnd, message_count=20):
        """최근 N개 메시지만 선택"""
        try:
            # 창에 포커스
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(DELAYS['focus_wait'])

            # 대화 영역 클릭 (하단 부근)
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.75)
            time.sleep(DELAYS['click_stabilize'])

            # 맨 아래 메시지에서 시작하여 위로 선택
            # 방법 1: Shift + Page Up을 여러 번 사용
            for _ in range(min(message_count // 5, 4)):  # 최대 4번, 대략 20개 메시지
                ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)  # Shift down
                ctypes.windll.user32.keybd_event(0x21, 0, 0, 0)  # Page Up down
                ctypes.windll.user32.keybd_event(0x21, 0, 2, 0)  # Page Up up
                ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)  # Shift up
                time.sleep(0.1)

            time.sleep(DELAYS['click_stabilize'])
            return True

        except Exception as e:
            print(f"메시지 선택 실패: {e}")
            return False

    @staticmethod
    def select_recent_messages_by_lines(hwnd, line_count=25):
        """라인 단위로 최근 메시지 선택"""
        try:
            # 창에 포커스
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(DELAYS['focus_wait'])

            # 대화 영역 하단 클릭
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.8)
            time.sleep(DELAYS['click_stabilize'])

            # 맨 아래에서 시작
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            ctypes.windll.user32.keybd_event(0x23, 0, 0, 0)  # End down
            ctypes.windll.user32.keybd_event(0x23, 0, 2, 0)  # End up
            ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            time.sleep(0.2)

            # Shift + 위쪽 화살표로 라인별 선택
            for _ in range(line_count):
                ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)  # Shift down
                ctypes.windll.user32.keybd_event(0x26, 0, 0, 0)  # Up arrow down
                ctypes.windll.user32.keybd_event(0x26, 0, 2, 0)  # Up arrow up
                ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)  # Shift up
                time.sleep(0.05)  # 빠른 선택

            time.sleep(DELAYS['click_stabilize'])
            return True

        except Exception as e:
            print(f"라인별 선택 실패: {e}")
            return False

    @staticmethod
    def find_chat_area_and_click(hwnd):
        """카카오톡 대화 영역을 찾아서 클릭"""
        try:
            rect = SafeWindowHandler.get_window_rect(hwnd)
            if not rect:
                return False

            for x_ratio, y_ratio in CHAT_AREA_POSITIONS:
                try:
                    if SafeWindowHandler.click_window_area(hwnd, x_ratio, y_ratio):
                        time.sleep(DELAYS['click_stabilize'])

                        # Ctrl+A를 눌러서 선택이 되는지 테스트
                        if SafeWindowHandler.safe_send_keys("^a"):
                            time.sleep(0.1)
                            return True
                except Exception as e:
                    print(f"클릭 위치 시도 실패: {e}")
                    continue

            return False

        except Exception as e:
            print(f"대화 영역 찾기 실패: {e}")
            return False

    @staticmethod
    def get_recent_chat_content(hwnd, method="smart_selection"):
        """최근 대화 내용만 가져오기 (여러 방법 지원)"""
        try:
            # 창에 포커스
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(DELAYS['focus_wait'])

            if method == "smart_selection":
                # 방법 1: 스마트 선택 (권장)
                success = SafeWindowHandler._smart_select_recent_messages(hwnd)
            elif method == "line_selection":
                # 방법 2: 라인별 선택
                success = SafeWindowHandler._line_based_selection(hwnd)
            elif method == "scroll_selection":
                # 방법 3: 스크롤 기반 선택
                success = SafeWindowHandler._scroll_based_selection(hwnd)
            else:
                # 기본: 전체 선택
                success = SafeWindowHandler.safe_send_keys("^a", hwnd)

            if success:
                time.sleep(DELAYS['click_stabilize'])
                return SafeWindowHandler.safe_send_keys("^c", hwnd)

            return False

        except Exception as e:
            print(f"최근 대화 가져오기 실패: {e}")
            return False

    @staticmethod
    def _smart_select_recent_messages(hwnd):
        """스마트 선택: 최근 메시지 영역만 선택"""
        try:
            # 대화창 하단 부근 클릭
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.75)
            time.sleep(DELAYS['click_stabilize'])

            # End 키로 맨 아래 이동
            ctypes.windll.user32.keybd_event(0x23, 0, 0, 0)  # End down
            ctypes.windll.user32.keybd_event(0x23, 0, 2, 0)  # End up
            time.sleep(0.2)

            # Shift + Ctrl + Home으로 제한된 영역 선택
            # 대신 Shift + Page Up을 3-4번 사용하여 적당한 양만 선택
            for i in range(3):  # 약 15-20개 메시지 정도
                ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)  # Shift down
                ctypes.windll.user32.keybd_event(0x21, 0, 0, 0)  # Page Up down
                ctypes.windll.user32.keybd_event(0x21, 0, 2, 0)  # Page Up up
                ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)  # Shift up
                time.sleep(0.15)

            return True

        except Exception as e:
            print(f"스마트 선택 실패: {e}")
            return False

    @staticmethod
    def _line_based_selection(hwnd):
        """라인 기반 선택: 정확한 라인 수만큼 선택"""
        try:
            # 대화창 클릭
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.7)
            time.sleep(DELAYS['click_stabilize'])

            # 맨 아래로 이동
            ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            ctypes.windll.user32.keybd_event(0x23, 0, 0, 0)  # End down
            ctypes.windll.user32.keybd_event(0x23, 0, 2, 0)  # End up
            ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            time.sleep(0.2)

            # 위로 20-25라인 선택
            for i in range(22):  # 22라인 정도 (약 20개 메시지)
                ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)  # Shift down
                ctypes.windll.user32.keybd_event(0x26, 0, 0, 0)  # Up arrow down
                ctypes.windll.user32.keybd_event(0x26, 0, 2, 0)  # Up arrow up
                ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)  # Shift up
                time.sleep(0.03)  # 빠른 선택

            return True

        except Exception as e:
            print(f"라인 기반 선택 실패: {e}")
            return False

    @staticmethod
    def _scroll_based_selection(hwnd):
        """스크롤 기반 선택: 스크롤을 이용한 영역 제한"""
        try:
            # 대화창 클릭
            SafeWindowHandler.click_window_area(hwnd, 0.5, 0.6)
            time.sleep(DELAYS['click_stabilize'])

            # 맨 아래로 스크롤
            for _ in range(5):  # 충분히 아래로
                ctypes.windll.user32.mouse_event(0x0800, 0, 0, -120, 0)  # 휠 다운
                time.sleep(0.1)

            # 마우스로 드래그 선택 (하단에서 상단으로)
            rect = SafeWindowHandler.get_window_rect(hwnd)
            if rect:
                start_x = rect['left'] + int(rect['width'] * 0.3)
                start_y = rect['top'] + int(rect['height'] * 0.8)  # 하단 80%
                end_x = rect['left'] + int(rect['width'] * 0.7)
                end_y = rect['top'] + int(rect['height'] * 0.4)  # 상단 40%

                # 드래그 시작
                ctypes.windll.user32.SetCursorPos(start_x, start_y)
                time.sleep(0.1)
                ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # 좌클릭 다운
                time.sleep(0.1)

                # 드래그
                ctypes.windll.user32.SetCursorPos(end_x, end_y)
                time.sleep(0.2)

                # 드래그 끝
                ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # 좌클릭 업
                time.sleep(0.2)

            return True

        except Exception as e:
            print(f"스크롤 기반 선택 실패: {e}")
            return False

    # 기존 메서드들 유지...
    @staticmethod
    def find_input_area_and_click(hwnd):
        """카카오톡 입력창을 찾아서 클릭"""
        try:
            rect = SafeWindowHandler.get_window_rect(hwnd)
            if not rect:
                return False

            for x_ratio, y_ratio in INPUT_AREA_POSITIONS:
                try:
                    if SafeWindowHandler.click_window_area(hwnd, x_ratio, y_ratio):
                        time.sleep(DELAYS['click_stabilize'])

                        # 입력창인지 테스트 (간단한 텍스트 입력 시도)
                        test_text = "test"

                        # 기존 내용 선택 후 테스트 텍스트 입력
                        SafeWindowHandler.safe_send_keys("^a")
                        time.sleep(0.1)

                        # 테스트 텍스트 입력
                        for char in test_text:
                            SafeWindowHandler.send_char(char)
                            time.sleep(0.05)

                        time.sleep(0.1)

                        # 테스트 텍스트 삭제 (Ctrl+A 후 Delete)
                        SafeWindowHandler.safe_send_keys("^a")
                        time.sleep(0.05)
                        ctypes.windll.user32.keybd_event(0x2E, 0, 0, 0)  # Delete down
                        ctypes.windll.user32.keybd_event(0x2E, 0, 2, 0)  # Delete up
                        time.sleep(0.1)

                        return True  # 입력이 성공했다면 입력창으로 간주
                except Exception as e:
                    print(f"입력창 테스트 실패: {e}")
                    continue

            return False

        except Exception as e:
            print(f"입력창 찾기 실패: {e}")
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
                time.sleep(DELAYS['focus_wait'])

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

            time.sleep(DELAYS['click_stabilize'])
            return True
        except Exception as e:
            print(f"키 입력 실패: {e}")
            return False

    @staticmethod
    def send_char(char):
        """개별 문자 입력"""
        try:
            # 유니코드 문자 입력
            ctypes.windll.user32.keybd_event(0, ord(char), 4, 0)  # KEYEVENTF_UNICODE
            time.sleep(DELAYS['key_input'])
        except Exception as e:
            print(f"문자 입력 실패: {e}")

    @staticmethod
    def send_enter():
        """엔터 키 입력"""
        try:
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter down
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter up
            return True
        except Exception as e:
            print(f"엔터 입력 실패: {e}")
            return False

    @staticmethod
    def is_window_valid(hwnd):
        """윈도우가 유효한지 확인"""
        try:
            return win32gui.IsWindow(hwnd)
        except:
            return False

    @staticmethod
    def focus_window(hwnd):
        """윈도우에 포커스 설정"""
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(DELAYS['focus_wait'])
            return True
        except Exception as e:
            print(f"포커스 설정 실패: {e}")
            return False