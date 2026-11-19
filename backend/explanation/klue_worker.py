"""Standalone KLUE worker, run by the previously prepared klue-cpu-venv Python.

Do not invoke as a public endpoint. Reads one UTF-8 JSON request from stdin,
returns one JSON list of p_support scores on stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: klue_worker.py MODEL_DIR APPLY_DIR")
    model_dir = Path(sys.argv[1])
    apply_dir = Path(sys.argv[2])
    data = json.load(sys.stdin)
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or not all(
        isinstance(p, list) and len(p) == 2 and all(isinstance(s, str) for s in p)
        for p in pairs
    ):
        raise ValueError("pairs must be [[sentence, evidence], ...]")
    sys.path.insert(0, str(apply_dir))
    from apply_model import load_model
    scorer = load_model(str(model_dir), batch=8)
    scores = scorer([tuple(p) for p in pairs])
    print(json.dumps([float(x) for x in scores], ensure_ascii=False))


if __name__ == "__main__":
    main()
