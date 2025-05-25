# window_scanner.py - 카카오톡 창 스캔 기능

import win32gui
from PyQt5.QtCore import QThread, pyqtSignal
from window_handler import SafeWindowHandler


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
                    if (self._is_kakao_window(title, process_name)):
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

    def _is_kakao_window(self, title, process_name):
        """카카오톡 창인지 판단"""
        kakao_indicators = [
            'kakaotalk' in process_name.lower(),
            'kakao' in process_name.lower(),
            '카카오톡' in title,
            # 카카오톡 대화방 제목 패턴 추가 가능
        ]
        return any(kakao_indicators)


class WindowManager:
    """윈도우 관리 클래스"""

    def __init__(self):
        self.kakao_windows = []
        self.selected_window = None
        self.scan_thread = WindowScanThread()

    def start_scanning(self, callback):
        """윈도우 스캔 시작"""
        self.scan_thread.windows_found.connect(callback)
        if not self.scan_thread.isRunning():
            self.scan_thread.start()

    def stop_scanning(self):
        """윈도우 스캔 중지"""
        if self.scan_thread.isRunning():
            self.scan_thread.quit()
            self.scan_thread.wait()

    def update_windows(self, windows):
        """발견된 창 목록 업데이트"""
        self.kakao_windows = windows

    def select_window(self, window_data):
        """창 선택"""
        self.selected_window = window_data
        if window_data:
            print(f"선택된 창: {window_data['title']}")

    def get_selected_hwnd(self):
        """선택된 창의 핸들 반환"""
        if self.selected_window:
            return self.selected_window['hwnd']
        return None

    def is_selected_window_valid(self):
        """선택된 창이 유효한지 확인"""
        hwnd = self.get_selected_hwnd()
        if hwnd:
            return SafeWindowHandler.is_window_valid(hwnd)
        return False

    def get_window_list(self):
        """창 목록 반환"""
        return self.kakao_windows

    def format_window_title(self, title, max_length=30):
        """창 제목 포맷팅"""
        if len(title) > max_length:
            return title[:max_length - 3] + "..."
        return title