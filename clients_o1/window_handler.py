import ctypes
import time
import win32gui
import win32process
import os
from ctypes import wintypes
from config import DELAYS, CHAT_AREA_POSITIONS, INPUT_AREA_POSITIONS


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