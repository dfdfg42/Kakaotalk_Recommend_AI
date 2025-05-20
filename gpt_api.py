import os
import json
from openai import OpenAI
import time
import sys
import codecs


class GPTFineTuner:
    def __init__(self, api_key=None, jsonl_file_path=None):
        """
        OpenAI GPT 파인튜닝 클래스 초기화

        Args:
            api_key (str): OpenAI API 키. 환경변수에서 자동으로 가져옵니다.
            jsonl_file_path (str): 파인튜닝용 JSONL 파일 경로
        """
        # 강력한 인코딩 설정
        self._configure_encoding()

        # API 키 설정
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("OpenAI API key required")

        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=self.api_key)

        # JSONL 파일 경로 설정
        if jsonl_file_path:
            self.jsonl_file_path = jsonl_file_path
        else:
            # 새로운 시스템 메시지가 포함된 파일로 설정
            self.jsonl_file_path = r"C:\Users\jang\PycharmProjects\PythonProject\DeepLearning\data\JangJaewon_multi_turn_no_system.jsonl"

        self.target_speaker = "KoKyungWoo"  # 영어로 변경
        self.model_id = None  # 파인튜닝된 모델 ID 저장

        # 프롬프트 제거 - 학습된 모델 그대로 사용

    def _configure_encoding(self):
        """강력한 인코딩 설정"""
        try:
            # 기본 인코딩 설정
            if sys.platform.startswith('win'):
                os.environ['PYTHONIOENCODING'] = 'utf-8'

                # stdout, stderr 인코딩 재설정
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8')
                    sys.stderr.reconfigure(encoding='utf-8')
                else:
                    # 구버전 파이썬용 대안
                    import codecs
                    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
                    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

                # Windows 콘솔 코드페이지 설정
                try:
                    os.system('chcp 65001 > nul')
                except:
                    pass
        except Exception as e:
            self.safe_print(f"Encoding setup error: {e}")

    def safe_print(self, text):
        """안전한 출력 함수"""
        try:
            print(text)
        except UnicodeEncodeError:
            # 인코딩 오류 시 안전하게 출력
            try:
                print(text.encode('utf-8', errors='ignore').decode('utf-8'))
            except:
                print(repr(text))

    def safe_input(self, prompt=""):
        """안전한 입력 함수"""
        try:
            return input(prompt)
        except UnicodeDecodeError:
            self.safe_print("Input encoding error. Please try again.")
            return ""

    def load_jsonl_data(self):
        """
        이미 변환된 JSONL 파일을 읽어서 검증

        Returns:
            int: 읽은 훈련 예시의 개수
        """
        self.safe_print(f"Loading JSONL file: {self.jsonl_file_path}")

        # 파일 존재 확인
        if not os.path.exists(self.jsonl_file_path):
            self.safe_print(f"JSONL file not found: {self.jsonl_file_path}")
            return 0

        try:
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            self.safe_print(f"Total training examples: {len(lines)}")

            # 데이터 형식 검증
            valid_examples = 0
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line)
                    # 필수 구조 확인
                    if 'messages' in data and isinstance(data['messages'], list):
                        if len(data['messages']) >= 2:
                            valid_examples += 1
                        else:
                            self.safe_print(f"Warning: Line {i + 1} has insufficient messages.")
                    else:
                        self.safe_print(f"Warning: Line {i + 1} has incorrect format.")
                except json.JSONDecodeError:
                    self.safe_print(f"Warning: Line {i + 1} has invalid JSON format.")

            self.safe_print(f"Valid training examples: {valid_examples}")

            # 처음 3개 예시 미리보기
            self.safe_print("\nFirst 3 examples:")
            for i, line in enumerate(lines[:3]):
                try:
                    data = json.loads(line)
                    self.safe_print(f"\nExample {i + 1}:")
                    self.safe_print(f"  User: {data['messages'][0]['content']}")
                    self.safe_print(f"  Assistant: {data['messages'][1]['content']}")
                except:
                    self.safe_print(f"  Example {i + 1}: Read error")

            return valid_examples

        except Exception as e:
            self.safe_print(f"Error reading JSONL file: {e}")
            return 0

    def upload_training_file(self, file_path):
        """
        OpenAI에 훈련 파일 업로드

        Args:
            file_path (str): 훈련 데이터 파일 경로

        Returns:
            str: 업로드된 파일 ID
        """
        with open(file_path, 'rb') as file:
            response = self.client.files.create(
                file=file,
                purpose='fine-tune'
            )

        file_id = response.id
        self.safe_print(f"File uploaded. File ID: {file_id}")
        return file_id

    def create_fine_tune_job(self, file_id):
        """
        파인튜닝 작업 생성

        Args:
            file_id (str): 업로드된 파일 ID

        Returns:
            str: 파인튜닝 작업 ID
        """
        response = self.client.fine_tuning.jobs.create(
            training_file=file_id,
            model="gpt-3.5-turbo"
        )

        job_id = response.id
        self.safe_print(f"Fine-tuning job started. Job ID: {job_id}")
        return job_id

    def check_fine_tune_status(self, job_id):
        """
        파인튜닝 상태 확인

        Args:
            job_id (str): 파인튜닝 작업 ID

        Returns:
            object: 파인튜닝 상태 정보
        """
        response = self.client.fine_tuning.jobs.retrieve(job_id)
        return response

    def wait_for_completion(self, job_id, check_interval=30):
        """
        파인튜닝 완료 대기

        Args:
            job_id (str): 파인튜닝 작업 ID
            check_interval (int): 상태 확인 간격 (초)
        """
        self.safe_print("Fine-tuning in progress...")

        while True:
            status = self.check_fine_tune_status(job_id)
            self.safe_print(f"Current status: {status.status}")

            if status.status == 'succeeded':
                self.model_id = status.fine_tuned_model
                self.safe_print(f"Fine-tuning completed! Model ID: {self.model_id}")
                break
            elif status.status == 'failed':
                self.safe_print("Fine-tuning failed.")
                self.safe_print(f"Error: {getattr(status, 'error', 'No info')}")
                break

            time.sleep(check_interval)

    def generate_response(self, prompt, max_tokens=150, temperature=0.8):
        """
        파인튜닝된 모델로 응답 생성
        - 모델이 시스템 메시지와 함께 파인튜닝되었으므로 별도의 시스템 메시지 추가 없음
        - 단순히 사용자 입력만 전달

        Args:
            prompt (str): 입력 메시지
            max_tokens (int): 최대 토큰 수
            temperature (float): 응답의 창의성 (0.0-2.0)

        Returns:
            str: 생성된 응답
        """
        if not self.model_id:
            self.safe_print("No fine-tuned model available. Please complete fine-tuning first.")
            return None

        try:
            # 단순한 메시지 구성 - 사용자 입력만 전달
            # (시스템 메시지는 이미 파인튜닝 데이터에 포함되어 있음)
            messages = [{"role": "user", "content": prompt}]

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # 응답 내용 추출 및 인코딩 처리
            response_content = response.choices[0].message.content

            # 응답이 None인 경우 처리
            if response_content is None:
                return "Unable to generate response."

            # 인코딩 안전성 확보
            try:
                # 유니코드 문자 정규화
                import unicodedata
                normalized = unicodedata.normalize('NFC', response_content)
                # 문제가 될 수 있는 문자 제거
                cleaned = normalized.encode('utf-8', errors='ignore').decode('utf-8')
                return cleaned
            except:
                # 정규화 실패 시 기본 문자열 반환
                return str(response_content)

        except Exception as e:
            error_msg = str(e)
            self.safe_print(f"Error generating response: {error_msg}")

            # 인코딩 관련 오류인 경우
            if 'codec' in error_msg or 'encode' in error_msg:
                self.safe_print("Encoding error. Please try again.")
                # 간단한 응답으로 대체
                return "Sorry, there was an issue generating the response."
            return None

    def run_full_pipeline(self):
        """
        JSONL 파일을 이용한 파인튜닝 파이프라인 실행
        """
        self.safe_print("=== GPT Fine-tuning Pipeline Started ===")

        # 1. JSONL 데이터 검증
        self.safe_print("\n1. Loading and validating JSONL file...")
        num_examples = self.load_jsonl_data()

        if num_examples == 0:
            self.safe_print("No valid training data found. Please check your JSONL file.")
            return

        self.safe_print(f"Number of examples for fine-tuning: {num_examples}")

        # 2. 파일 업로드
        self.safe_print("\n2. Uploading training file...")
        file_id = self.upload_training_file(self.jsonl_file_path)

        # 3. 파인튜닝 작업 생성
        self.safe_print("\n3. Creating fine-tuning job...")
        job_id = self.create_fine_tune_job(file_id)

        # 4. 파인튜닝 완료 대기
        self.safe_print("\n4. Waiting for fine-tuning completion...")
        self.wait_for_completion(job_id)

        self.safe_print("\n=== Fine-tuning Pipeline Completed ===")

        if self.model_id:
            self.safe_print(f"\nFine-tuned Model ID: {self.model_id}")
            self.safe_print("You can now chat with this model.")
            self.safe_print("Run fine_tuner.interactive_chat() to start chatting.")

    def interactive_chat(self):
        """
        파인튜닝된 모델과의 대화형 채팅 (프롬프트 없이)
        """
        if not self.model_id:
            self.safe_print("No fine-tuned model available. Please complete fine-tuning first.")
            return

        self.safe_print(f"\n=== Chat with {self.target_speaker} ===")
        self.safe_print(f"Model ID: {self.model_id}")
        self.safe_print("\nCommands:")
        self.safe_print("- 'quit' or 'exit': End chat")
        self.safe_print("")

        while True:
            user_input = self.safe_input("You: ")

            if not user_input:  # 입력 오류 시
                continue

            # 명령어 처리
            if user_input.lower() in ['quit', 'exit']:
                self.safe_print("Ending chat.")
                break

            # 일반 대화 처리 - 단순히 사용자 입력을 모델에 전달
            response = self.generate_response(user_input)
            if response:
                self.safe_print(f"{self.target_speaker}: {response}\n")
            else:
                self.safe_print("Failed to generate response.\n")


def main():
    """
    메인 함수 - JSONL 파일을 이용한 파인튜닝 또는 기존 모델 사용
    """
    # OpenAI API 키 설정 (환경변수나 직접 입력)
    # 여기에 직접 API 키를 입력하세요
    api_key = ""  # sk-로 시작하는 키를 입력

    # === 새로운 파인튜닝을 위해 기존 모델 ID 주석 처리 ===
    existing_model_id = "" # 기존 모델
    # existing_model_id = "ft:gpt-3.5-turbo-0125:jangjaewon::BX4NCBO4"  # 새로 파인튜닝할 때 None으로 설정

    # JSONL 파일 절대 경로 - 시스템 메시지가 포함된 새 파일
    jsonl_file_path = r"C:\Users\jang\PycharmProjects\PythonProject\DeepLearning\data\JangJaewon_multi_turn_no_system.jsonl"

    # GPT 파인튜너 초기화
    fine_tuner = GPTFineTuner(api_key, jsonl_file_path)

    # 기존 모델이 있으면 바로 사용, 없으면 파인튜닝 진행
    if existing_model_id:
        fine_tuner.safe_print(f"Using existing fine-tuned model: {existing_model_id}")
        fine_tuner.model_id = existing_model_id

        # 바로 채팅 시작
        user_input = fine_tuner.safe_input("Start interactive chat? (y/n): ")

        if user_input.lower() in ['y', 'yes']:
            fine_tuner.interactive_chat()
        else:
            fine_tuner.safe_print("Run fine_tuner.interactive_chat() when you want to chat.")
    else:
        # 새로 파인튜닝 진행
        fine_tuner.safe_print("Starting new fine-tuning...")
        fine_tuner.run_full_pipeline()

        # 파인튜닝 완료 후 대화형 채팅 시작
        if fine_tuner.model_id:
            fine_tuner.safe_print("\nFine-tuning completed!")
            fine_tuner.safe_print(f"New Model ID: {fine_tuner.model_id}")
            fine_tuner.safe_print("Save this model ID to use it next time.")
            user_input = fine_tuner.safe_input("Start interactive chat? (y/n): ")

            if user_input.lower() in ['y', 'yes']:
                fine_tuner.interactive_chat()
            else:
                fine_tuner.safe_print(f"Fine-tuned Model ID: {fine_tuner.model_id}")
                fine_tuner.safe_print("Run fine_tuner.interactive_chat() later to chat.")


if __name__ == "__main__":
    main()