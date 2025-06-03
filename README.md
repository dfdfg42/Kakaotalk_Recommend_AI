카카오톡 챗봇 사용법

1. config 설정
   # OpenAI API 키 설정
   OPENAI_API_KEY = ""  # 여기에 본인 API KETY 넣으시면 됩니다

   # GPT 설정
  GPT_TEMPERATURE = 0.8 # 창의성 조정. 높을수록 창의적
  GPT_MAX_TOKENS = 80 # 답변 길이 조정. 높을수록 긴 답

  # 파인튜닝된 모델 설정
  USE_FINE_TUNED_MODEL = True # True로 설정하면 파인튜닝된 모델 사용. False시 기본 모델 사용
  FINE_TUNED_MODEL_ID = ""  # 파인튜닝된 모델 ID (예: "ft:gpt-3.5-turbo-0125:...")

  # 파싱 형식 설정(count / date)
  PARSER_TYPE = "date"  # "count" 또는 "date"

  # count: 최근 N개 메시지 기준 파싱 (chat_parser.py)
  # date: 최근 하루 기준 파싱 (chat_date_parser.py)

  # 개수 기반 파싱 설정 (PARSER_TYPE = "count"일 때)
  MAX_RECENT_MESSAGES = 20  # 최근 몇 개 메시지까지 가져올지

  # 날짜 기반 파싱 설정 (PARSER_TYPE = "date"일 때)
  DATE_LIMIT_HOURS = 24  # 최근 몇 시간까지 가져올지 (기본 24시간 = 하루)

  # 프롬프트 설정(시스템 / 고경우)
  
  SYSTEM_PROMPT / KOKYUNGWOO_PROMPT => 시스템 / 고경우. # 파인튜닝 모델 사용하면 자동으로 고경우 프롬프트 사용
