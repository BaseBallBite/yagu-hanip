"""AI-A 해설 생성 설정. 여기 값만 바꾸면 됨."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ── 모델 ─────────────────────────────────────────────
# 실험 내내 모델 하나로 고정해야 B0~B3 비교가 공정함. 중간에 바꾸지 말 것.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

# 프롬프트를 고치면 반드시 올릴 것. 캐시 키에 들어가서 옛 결과가 섞이지 않음.
PROMPT_VERSION = "v1"

# 생성 설정
TEMPERATURE = None          # None이면 모델 기본값 사용 (Gemini 3 계열은 기본값 권장)
SEED = 42
MAX_OUTPUT_TOKENS = 2048
THINKING_BUDGET = None         # 2.5 계열: 0이면 thinking 끔 (thinking 토큰도 출력 요금으로 과금됨)
THINKING_LEVEL = "low"       # 3 계열: "low" 등. 쓰면 THINKING_BUDGET은 None으로

# ── 한도 대응 ─────────────────────────────────────────
RPM = int(os.environ.get("GEMINI_RPM", "8"))   # AI Studio에 뜨는 RPM보다 조금 낮게
MAX_RETRIES = 6
BACKOFF_BASE = 4.0          # 초. 4, 8, 16, 32 ... + 랜덤 지터
BACKOFF_MAX = 90.0
RETRY_CODES = {429, 500, 503, 504}

# ── 경로 ─────────────────────────────────────────────
CACHE_DIR = ROOT / "cache"
LOG_DIR = ROOT / "logs"
OUT_DIR = ROOT / "outputs"
USAGE_LOG = LOG_DIR / "usage.jsonl"

# ── 요금 (USD / 1M 토큰) ──────────────────────────────
# 2026-11-03 기준 공개 단가. 쓰기 전에 ai.google.dev/gemini-api/docs/pricing 에서 꼭 다시 확인.
# 3.6~3.8 Flash는 2027-01-01부터 두 배($1.50 / $7.50)로 오른다고 공지됨.
PRICES = {
    "gemini-3.8-flash": {"in": 0.75, "out": 3.75},
    "gemini-2.5-flash-lite": {"in": 0.10, "out": 0.40},
    "gemini-2.5-flash":      {"in": 0.30, "out": 2.50},
    "gemini-3.1-flash-lite": {"in": 0.25, "out": 1.50},
    # 실제 쓰는 3.x Flash 모델 ID를 확인해서 추가: 예) "gemini-3.6-flash": {"in": 0.75, "out": 3.75},
}
KRW_PER_USD = 1450
