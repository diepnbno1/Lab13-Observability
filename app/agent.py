from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM, FakeResponse
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import get_langfuse_client, observe


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe(name="agent.run", capture_input=False, capture_output=False)
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        docs = self._retrieve(message)
        prompt = self._build_prompt(feature=feature, docs=docs, message=message)
        response = self._generate(prompt)
        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        client = get_langfuse_client()
        if client is not None:
            client.update_current_trace(
                name="chat_request",
                user_id=hash_user_id(user_id),
                session_id=session_id,
                tags=["lab", feature, self.model],
                metadata={
                    "feature": feature,
                    "model": self.model,
                    "query_preview": summarize_text(message),
                },
            )
            client.update_current_span(
                metadata={
                    "latency_ms": latency_ms,
                    "quality_score": quality_score,
                    "cost_usd": cost_usd,
                    "doc_count": len(docs),
                }
            )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    @observe(name="rag.retrieve", capture_input=False, capture_output=False)
    def _retrieve(self, message: str) -> list[str]:
        docs = retrieve(message)
        client = get_langfuse_client()
        if client is not None:
            client.update_current_span(
                metadata={
                    "tool_name": "mock_rag",
                    "doc_count": len(docs),
                    "query_preview": summarize_text(message),
                }
            )
        return docs

    @observe(name="llm.generate", as_type="generation", capture_input=False, capture_output=False)
    def _generate(self, prompt: str) -> FakeResponse:
        response = self.llm.generate(prompt)
        client = get_langfuse_client()
        if client is not None:
            client.update_current_generation(
                model=response.model,
                usage_details={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                cost_details={
                    "total": self._estimate_cost(
                        response.usage.input_tokens,
                        response.usage.output_tokens,
                    )
                },
                metadata={"prompt_preview": summarize_text(prompt)},
            )
        return response

    def _build_prompt(self, feature: str, docs: list[str], message: str) -> str:
        compact_docs = " ".join(docs[:2])[:600]
        compact_question = message.strip()[:400]
        return f"Feature={feature}\nDocs={compact_docs}\nQuestion={compact_question}"

    def legacy_prompt_cost_estimate(self, feature: str, docs: list[str], message: str) -> tuple[int, int]:
        legacy_prompt = f"Feature={feature}\nDocs={docs}\nQuestion={message}"
        optimized_prompt = self._build_prompt(feature=feature, docs=docs, message=message)
        return max(20, len(legacy_prompt) // 4), max(20, len(optimized_prompt) // 4)

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
