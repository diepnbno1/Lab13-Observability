from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from threading import Lock


@dataclass
class MetricSample:
    ts: datetime
    latency_ms: int
    cost_usd: float
    tokens_in: int
    tokens_out: int
    quality_score: float


@dataclass
class ErrorSample:
    ts: datetime
    error_type: str

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []
REQUEST_SAMPLES: list[MetricSample] = []
ERROR_SAMPLES: list[ErrorSample] = []
LOCK = Lock()


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    with LOCK:
        TRAFFIC += 1
        REQUEST_LATENCIES.append(latency_ms)
        REQUEST_COSTS.append(cost_usd)
        REQUEST_TOKENS_IN.append(tokens_in)
        REQUEST_TOKENS_OUT.append(tokens_out)
        QUALITY_SCORES.append(quality_score)
        REQUEST_SAMPLES.append(
            MetricSample(
                ts=datetime.now(timezone.utc),
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                quality_score=quality_score,
            )
        )



def record_error(error_type: str) -> None:
    with LOCK:
        ERRORS[error_type] += 1
        ERROR_SAMPLES.append(ErrorSample(ts=datetime.now(timezone.utc), error_type=error_type))



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    with LOCK:
        total_errors = sum(ERRORS.values())
        total_attempts = TRAFFIC + total_errors
        return {
            "traffic": TRAFFIC,
            "latency_p50": percentile(REQUEST_LATENCIES, 50),
            "latency_p95": percentile(REQUEST_LATENCIES, 95),
            "latency_p99": percentile(REQUEST_LATENCIES, 99),
            "error_rate_pct": round((total_errors / total_attempts) * 100, 2) if total_attempts else 0.0,
            "avg_cost_usd": round(mean(REQUEST_COSTS), 6) if REQUEST_COSTS else 0.0,
            "total_cost_usd": round(sum(REQUEST_COSTS), 6),
            "tokens_in_total": sum(REQUEST_TOKENS_IN),
            "tokens_out_total": sum(REQUEST_TOKENS_OUT),
            "error_breakdown": dict(ERRORS),
            "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
        }


def dashboard_payload(minutes: int = 60) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    with LOCK:
        samples = [asdict(sample) for sample in REQUEST_SAMPLES if sample.ts >= cutoff]
        errors = [asdict(sample) for sample in ERROR_SAMPLES if sample.ts >= cutoff]

    for sample in samples:
        sample["ts"] = sample["ts"].isoformat()
    for error in errors:
        error["ts"] = error["ts"].isoformat()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_minutes": minutes,
        "refresh_seconds": 15,
        "slo": {
            "latency_p95_ms": 3000,
            "error_rate_pct": 2,
            "daily_cost_usd": 2.5,
            "quality_score_avg": 0.75,
        },
        "snapshot": snapshot(),
        "series": samples,
        "errors": errors,
    }
