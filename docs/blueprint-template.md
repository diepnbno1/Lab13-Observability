# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Solo - Nguyen Bach Diep
- [REPO_URL]: https://github.com/diepnbno1/Lab13-Observability
- [MEMBERS]:
  - Member A: Nguyen Bach Diep | Student ID: 2A202600535 | Role: Logging & PII
  - Member B: Nguyen Bach Diep | Student ID: 2A202600535 | Role: Tracing & Enrichment
  - Member C: Nguyen Bach Diep | Student ID: 2A202600535 | Role: SLO & Alerts
  - Member D: Nguyen Bach Diep | Student ID: 2A202600535 | Role: Load Test & Dashboard
  - Member E: Nguyen Bach Diep | Student ID: 2A202600535 | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 20+ verified via Langfuse Public API (`docs/evidence/runtime_summary.json`)
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/evidence/logs-correlation-id.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/evidence/logs-pii-redaction.png
- [EVIDENCE_TRACE_LIST_SCREENSHOT]: docs/evidence/langfuse-trace-list-ui.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/evidence/langfuse-trace-waterfall-ui.png
- [TRACE_WATERFALL_EXPLANATION]: The `rag_slow` trace shows `rag.retrieve` taking about 2.501s inside the `agent.run` trace, while `llm.generate` stays around 0.152s. This proves the latency incident is caused by retrieval, not generation.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/dashboard-6-panels.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 2653ms |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $2.5/day | 1d | $0.065139 observed in demo |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/evidence/alert-rules-runbook.png
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Tail latency increased during incident injection. Runtime summary recorded incident latency of 2655ms and dashboard showed P99 near 2655ms.
- [ROOT_CAUSE_PROVED_BY]: Langfuse trace `4d43c4393a7c9bd8d1be1bcbdb954794` and `docs/evidence/langfuse-trace-waterfall-ui.png` show `rag.retrieve` as the slow span. Runtime evidence in `docs/evidence/runtime_summary.json` records incident correlation ID `req-5519de54`.
- [FIX_ACTION]: Disabled the `rag_slow` incident toggle and documented retrieval mitigations: truncate long queries, use fallback retrieval source, and reduce prompt size.
- [PREVENTIVE_MEASURE]: Keep the high-latency P95 alert active with a runbook that compares RAG span duration against LLM generation duration.

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME] Nguyen Bach Diep - 2A202600535
- [TASKS_COMPLETED]: Implemented correlation ID propagation, structured JSON logs, recursive PII redaction, audit log output, and Langfuse-safe trace metadata.
- [EVIDENCE_LINK]: Commit `c9cd2f8` - Implement core observability instrumentation

### [MEMBER_B_NAME] Nguyen Bach Diep - 2A202600535
- [TASKS_COMPLETED]: Added nested Langfuse spans for `agent.run`, `rag.retrieve`, and `llm.generate`, verified 20+ live traces through Langfuse API.
- [EVIDENCE_LINK]: Commit `c9cd2f8` - Implement core observability instrumentation

### [MEMBER_C_NAME] Nguyen Bach Diep - 2A202600535
- [TASKS_COMPLETED]: Configured SLO targets, alert owners, three alert rules, and runbook evidence.
- [EVIDENCE_LINK]: Files `config/slo.yaml`, `config/alert_rules.yaml`, and `docs/alerts.md`

### [MEMBER_D_NAME] Nguyen Bach Diep - 2A202600535
- [TASKS_COMPLETED]: Built local dashboard with 6 required panels, one-hour window, 15-second refresh, units, SLO thresholds, and generated dashboard evidence.
- [EVIDENCE_LINK]: Commit `e10b159` - Add local observability dashboard

### [MEMBER_E_NAME] Nguyen Bach Diep - 2A202600535
- [TASKS_COMPLETED]: Ran load tests, injected `rag_slow`, collected runtime evidence, wrote incident response, and prepared submission artifacts.
- [EVIDENCE_LINK]: `docs/evidence/runtime_summary.json`

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Compact prompt construction reduces measured input tokens from 340 to 330 on the sample set, saving 2.94% input-token cost. Evidence: `docs/evidence/cost_comparison.json`.
- [BONUS_DASHBOARD_QUALITY]: Professional 6-panel local dashboard with clear units, SLO lines, refresh status, and screenshot evidence at `docs/evidence/dashboard-6-panels.png`.
- [BONUS_AUTOMATION]: Custom script `scripts/run_observability_demo.py` sends sample requests, injects incident, validates logs, checks Langfuse traces, and writes `docs/evidence/runtime_summary.json`.
- [BONUS_AUDIT_LOGS]: Separate audit events are written to `data/audit.jsonl` for completed chats, failed chats, and incident toggle actions. Sanitized evidence sample: `docs/evidence/audit-log-sample.jsonl`.
