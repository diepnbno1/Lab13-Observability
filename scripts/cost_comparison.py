from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent import LabAgent
from app.mock_rag import retrieve


QUERIES = Path("data/sample_queries.jsonl")
OUTPUT = Path("docs/evidence/cost_comparison.json")
INPUT_COST_PER_MILLION = 3.0


def main() -> None:
    agent = LabAgent()
    rows = []
    legacy_total = 0
    optimized_total = 0

    for line in QUERIES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        docs = retrieve(payload["message"])
        legacy_tokens, optimized_tokens = agent.legacy_prompt_cost_estimate(
            feature=payload["feature"],
            docs=docs,
            message=payload["message"],
        )
        legacy_total += legacy_tokens
        optimized_total += optimized_tokens
        rows.append(
            {
                "session_id": payload["session_id"],
                "feature": payload["feature"],
                "legacy_input_tokens": legacy_tokens,
                "optimized_input_tokens": optimized_tokens,
                "input_token_delta": legacy_tokens - optimized_tokens,
            }
        )

    legacy_cost = (legacy_total / 1_000_000) * INPUT_COST_PER_MILLION
    optimized_cost = (optimized_total / 1_000_000) * INPUT_COST_PER_MILLION
    savings_pct = ((legacy_cost - optimized_cost) / legacy_cost) * 100 if legacy_cost else 0.0

    report = {
        "method": "Compare legacy prompt construction with compact prompt construction on sample_queries.jsonl.",
        "legacy_input_tokens": legacy_total,
        "optimized_input_tokens": optimized_total,
        "legacy_input_cost_usd": round(legacy_cost, 6),
        "optimized_input_cost_usd": round(optimized_cost, 6),
        "savings_pct": round(savings_pct, 2),
        "rows": rows,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
