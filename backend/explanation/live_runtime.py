"""Production-wiring adapter: existing AI-A GeminiRunner + separate KLUE CPU environment.

Keep heavyweight Torch/transformers out of the FastAPI .venv. A short-lived model
subprocess per scored batch is intentional for this first integration; no scores
are fabricated and failed inference never bypasses verification.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from backend.explanation.service_pipeline import load_threshold

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "backend" / "explanation" / "klue_worker.py"


@dataclass(frozen=True)
class LiveDependencies:
    generate: Callable
    p_support: Callable
    threshold: float


def score_with_klue_subprocess(pairs: list[tuple[str, str]], *, python: Path,
                               model_dir: Path, apply_dir: Path) -> list[float]:
    """Real KLUE inference in its own existing virtual environment; UTF-8 over stdin."""
    if not pairs:
        return []
    payload = json.dumps({"pairs": pairs}, ensure_ascii=False)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    try:
        proc = subprocess.run(
            [str(python), str(WORKER), str(model_dir), str(apply_dir)],
            input=payload, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=180, env=env, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("KLUE 검증 프로세스를 실행할 수 없습니다") from exc
    if proc.returncode != 0:
        raise RuntimeError("KLUE 검증 프로세스가 실패했습니다")
    try:
        scores = json.loads(proc.stdout.strip().splitlines()[-1])
        if not isinstance(scores, list):
            raise ValueError("expected a list")
        return scores
    except (ValueError, IndexError) as exc:
        raise RuntimeError("KLUE 검증 결과가 올바른 JSON 목록이 아닙니다") from exc


def _new_gemini_runner():
    """Import AI-A's existing script-compatible gemini_client without modifying it.

    AI-A currently uses 'import config' as a top-level import. Its script folder
    must be importable in service mode as well.
    """
    ai_dir = ROOT / "ai" / "explain"
    if str(ai_dir) not in sys.path:
        sys.path.insert(0, str(ai_dir))
    from ai.explain.gemini_client import GeminiRunner
    return GeminiRunner()


@lru_cache(maxsize=1)
def get_live_dependencies() -> LiveDependencies:
    """Validate paths and API-key setting on the first *actual live* request."""
    model_s = os.environ.get("KLUE_MODEL_DIR", "")
    apply_s = os.environ.get("KLUE_APPLY_DIR", "")
    python_s = os.environ.get("KLUE_PYTHON", "")
    if not all((model_s, apply_s, python_s)):
        raise RuntimeError("KLUE_MODEL_DIR, KLUE_APPLY_DIR, KLUE_PYTHON 설정이 필요합니다")
    model_dir, apply_dir, python = Path(model_s), Path(apply_s), Path(python_s)
    if not (model_dir / "model.safetensors").is_file() or not (model_dir / "threshold.json").is_file():
        raise RuntimeError("KLUE 모델 파일이 없습니다")
    if not (apply_dir / "apply_model.py").is_file() or not python.is_file():
        raise RuntimeError("KLUE 실행 환경 또는 apply_model.py가 없습니다")
    threshold = load_threshold(model_dir)
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY 환경 변수 설정이 필요합니다")
    runner = _new_gemini_runner()
    return LiveDependencies(
        generate=runner.generate,
        p_support=lambda pairs: score_with_klue_subprocess(
            pairs, python=python, model_dir=model_dir, apply_dir=apply_dir
        ),
        threshold=threshold,
    )
