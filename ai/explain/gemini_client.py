"""Gemini 호출 래퍼: 캐시 → 속도 제한 → 호출 → 429/503 재시도 → 사용량 기록."""
import hashlib
import json
import random
import re
import time
from datetime import datetime, timezone

import config


class DailyQuotaExceeded(RuntimeError):
    """하루 한도(RPD) 소진. 재시도해도 소용없으니 멈추고 내일(태평양 자정) 이어서 돌림."""


def price_of(model):
    p = config.PRICES.get(model)
    if p is None:
        print(f"[경고] {model} 단가가 config.PRICES에 없음 → 비용 0으로 기록됨")
        return {"in": 0.0, "out": 0.0}
    return p


def cost_usd(model, prompt_tokens, output_tokens):
    """output_tokens = 답변 + thinking 토큰 (둘 다 출력 단가로 과금)."""
    p = price_of(model)
    return prompt_tokens / 1e6 * p["in"] + output_tokens / 1e6 * p["out"]


def _cache_key(payload):
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()[:32]


def _parse_retry_delay(err_text):
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", err_text)
    return float(m.group(1)) if m else None


def _is_daily_quota(err_text):
    return bool(re.search(r"PerDay|per_day|requests_per_day", err_text, re.I))


class GeminiRunner:
    def __init__(self, model=config.MODEL, dry_run=False):
        self.model = model
        self.dry_run = dry_run
        self._last_call = 0.0
        self._min_interval = 60.0 / max(config.RPM, 1)
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            from google import genai
            self.client = genai.Client()  # GEMINI_API_KEY 환경변수 사용

    # ── 내부 ──
    def _gen_config(self, schema):
        from google.genai import types
        thinking = None
        if config.THINKING_LEVEL is not None:
            thinking = types.ThinkingConfig(thinking_level=config.THINKING_LEVEL)
        elif config.THINKING_BUDGET is not None:
            thinking = types.ThinkingConfig(thinking_budget=config.THINKING_BUDGET)
        return types.GenerateContentConfig(
            system_instruction=self._system,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=config.TEMPERATURE,
            seed=config.SEED,
            max_output_tokens=config.MAX_OUTPUT_TOKENS,
            thinking_config=thinking,
        )

    def _throttle(self):
        if self.dry_run:
            return
        wait = self._min_interval - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()

    def _log(self, rec):
        rec["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(config.USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _fake_response(self, user_prompt):
        ids = re.findall(r"^([A-Za-z][\w.]*):", user_prompt, re.M)
        sents = [{"text": f"(dry-run) {i} 근거 문장입니다.", "evidence": [i]} for i in ids[:3]]
        sents.append({"text": "(dry-run) 이 부분은 기록에 없어 알 수 없습니다.", "evidence": ["UNKNOWN"]})
        return json.dumps({"sentences": sents}, ensure_ascii=False), len(user_prompt) // 2, 120, 0

    # ── 공개 ──
    def generate(self, system, user_prompt, schema, tag):
        """tag: {'qid':..., 'condition':...} 로그용. 반환: (dict 결과, 메타)"""
        self._system = system
        key = _cache_key({"model": self.model, "pv": config.PROMPT_VERSION, "sys": system,
                          "user": user_prompt, "temp": config.TEMPERATURE, "seed": config.SEED,
                          "tb": config.THINKING_BUDGET, "tl": config.THINKING_LEVEL,
                          "dry": self.dry_run})
        cache_file = config.CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            c = json.loads(cache_file.read_text(encoding="utf-8"))
            self._log({**tag, "model": self.model, "cache_hit": True, "status": "ok",
                       "prompt_tokens": 0, "output_tokens": 0, "thoughts_tokens": 0,
                       "cost_usd": 0.0, "attempts": 0, "latency_s": 0.0, "cache_key": key})
            return c["parsed"], {**c["meta"], "cache_hit": True}

        attempts = 0
        while True:
            attempts += 1
            self._throttle()
            t0 = time.time()
            try:
                if self.dry_run:
                    text, p_tok, c_tok, th_tok = self._fake_response(user_prompt)
                else:
                    resp = self.client.models.generate_content(
                        model=self.model, contents=user_prompt, config=self._gen_config(schema))
                    text = resp.text
                    u = resp.usage_metadata
                    p_tok = u.prompt_token_count or 0
                    c_tok = u.candidates_token_count or 0
                    th_tok = u.thoughts_token_count or 0
                break
            except Exception as e:  # google.genai.errors.APIError 포함
                code = getattr(e, "code", None)
                err_text = str(getattr(e, "details", "")) + " " + str(e)
                if code == 429 and _is_daily_quota(err_text):
                    self._log({**tag, "model": self.model, "cache_hit": False, "status": "daily_quota",
                               "attempts": attempts, "error": err_text[:300]})
                    raise DailyQuotaExceeded(err_text[:300]) from e
                if code not in config.RETRY_CODES or attempts > config.MAX_RETRIES:
                    self._log({**tag, "model": self.model, "cache_hit": False, "status": f"error_{code}",
                               "attempts": attempts, "error": err_text[:300]})
                    raise
                delay = _parse_retry_delay(err_text)
                if delay is None:
                    delay = min(config.BACKOFF_BASE * 2 ** (attempts - 1), config.BACKOFF_MAX)
                delay += random.uniform(0, 2)
                print(f"  [{code}] {tag} {attempts}번째 실패 → {delay:.0f}초 후 재시도")
                self._log({**tag, "model": self.model, "cache_hit": False, "status": f"retry_{code}",
                           "attempts": attempts, "wait_s": round(delay, 1)})
                time.sleep(delay)

        latency = time.time() - t0
        parsed = json.loads(text)
        out_tok = c_tok + th_tok
        meta = {"model": self.model, "prompt_tokens": p_tok, "output_tokens": c_tok,
                "thoughts_tokens": th_tok, "cost_usd": cost_usd(self.model, p_tok, out_tok),
                "latency_s": round(latency, 2), "attempts": attempts}
        cache_file.write_text(json.dumps({"parsed": parsed, "raw_text": text, "meta": meta},
                                         ensure_ascii=False, indent=1), encoding="utf-8")
        self._log({**tag, **meta, "cache_hit": False, "status": "ok", "cache_key": key})
        return parsed, {**meta, "cache_hit": False}
