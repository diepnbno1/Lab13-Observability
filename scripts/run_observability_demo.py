from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values


BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")
OUTPUT = Path("docs/evidence/runtime_summary.json")


def post_json(client: httpx.Client, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    response = client.post(f"{BASE_URL}{path}", json=payload, timeout=30.0)
    response.raise_for_status()
    return response.json()


def get_json(client: httpx.Client, path: str) -> dict[str, Any]:
    response = client.get(f"{BASE_URL}{path}", timeout=30.0)
    response.raise_for_status()
    return response.json()


def load_queries() -> list[dict[str, Any]]:
    return [json.loads(line) for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_validate_logs() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "scripts/validate_logs.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    score = None
    for line in result.stdout.splitlines():
        if line.startswith("Estimated Score:"):
            score = int(line.split(":", 1)[1].split("/", 1)[0].strip())
    return {
        "returncode": result.returncode,
        "estimated_score": score,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def query_langfuse_traces() -> dict[str, Any]:
    env = dotenv_values(".env")
    public_key = env.get("LANGFUSE_PUBLIC_KEY")
    secret_key = env.get("LANGFUSE_SECRET_KEY")
    host = (env.get("LANGFUSE_HOST") or "https://cloud.langfuse.com").rstrip("/")

    if not public_key or not secret_key:
        return {"ok": False, "reason": "missing_keys", "records_returned": 0}

    try:
        response = httpx.get(
            f"{host}/api/public/traces",
            params={"limit": 20},
            auth=(public_key, secret_key),
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        records = payload.get("data", payload)
        return {
            "ok": True,
            "records_returned": len(records) if isinstance(records, list) else 0,
            "limit": 20,
        }
    except Exception as exc:
        return {"ok": False, "reason": type(exc).__name__, "records_returned": 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=2, help="How many times to send sample queries")
    args = parser.parse_args()

    sent = []
    queries = load_queries()

    with httpx.Client(timeout=30.0) as client:
        health = get_json(client, "/health")
        for round_index in range(args.rounds):
            for payload in queries:
                started = time.perf_counter()
                result = post_json(client, "/chat", payload)
                sent.append(
                    {
                        "round": round_index + 1,
                        "session_id": payload["session_id"],
                        "feature": payload["feature"],
                        "correlation_id": result["correlation_id"],
                        "latency_ms": result["latency_ms"],
                        "client_latency_ms": int((time.perf_counter() - started) * 1000),
                    }
                )

        post_json(client, "/incidents/rag_slow/enable")
        incident_payload = {
            "user_id": "u_incident",
            "session_id": "s_incident_rag_slow",
            "feature": "qa",
            "message": "Explain why metrics traces and logs work together during a latency incident.",
        }
        incident_result = post_json(client, "/chat", incident_payload)
        post_json(client, "/incidents/rag_slow/disable")

        metrics = get_json(client, "/metrics")
        dashboard = get_json(client, "/dashboard/data")

    validate = run_validate_logs()
    langfuse = query_langfuse_traces()

    summary = {
        "health": health,
        "requests_sent": len(sent),
        "sample_trace_candidates": sent[:5],
        "incident": {
            "scenario": "rag_slow",
            "correlation_id": incident_result["correlation_id"],
            "latency_ms": incident_result["latency_ms"],
            "expected_root_cause": "Retrieval latency spike in rag.retrieve span.",
        },
        "metrics": metrics,
        "dashboard": {
            "window_minutes": dashboard["window_minutes"],
            "refresh_seconds": dashboard["refresh_seconds"],
            "panel_count": 6,
            "slo": dashboard["slo"],
        },
        "validate_logs": validate,
        "langfuse_trace_check": langfuse,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
