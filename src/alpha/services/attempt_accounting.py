"""
Audit and accounting pipeline for raw episode attempts.

Audits all raw attempts (e.g. 169 pilot records in data/raw/pilot/phase_a_pilot/episodes.jsonl),
categorizes each attempt (crashed, completed, aborted), and generates:
1. All-attempts accounting (demonstrating true reliability including rejected attempts).
2. Accepted-episodes accounting (with explicit, defensible filter criteria).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AttemptAuditRecord:
    episode_id: str
    experiment_id: str
    recorded_at: str
    seed: int | None
    agent_name: str
    model_identifier: str
    fault_type: str
    fault_intensity: float
    total_sim_steps: int
    total_wall_seconds: float
    success: bool
    crashed: bool
    timed_out: bool
    failure_reason: str
    is_accepted: bool
    rejection_reason: str
    status: str  # "completed", "crashed", "aborted", "timed_out"


@dataclass
class AccountingSummary:
    total_attempts: int
    accepted_attempts: int
    rejected_attempts: int
    all_attempts_crash_rate: float
    all_attempts_success_rate: float
    accepted_crash_rate: float
    accepted_success_rate: float
    rejection_reasons: dict[str, int]
    by_agent: dict[str, dict[str, Any]]
    by_fault_accepted: dict[str, dict[str, Any]]


class AttemptAccountingAuditor:
    """Processes raw jsonl logs and produces comprehensive attempt accounting."""

    def __init__(self, jsonl_path: str = "data/raw/pilot/phase_a_pilot/episodes.jsonl") -> None:
        self.jsonl_path = Path(jsonl_path)
        self.records: list[AttemptAuditRecord] = []

    def audit(self) -> list[AttemptAuditRecord]:
        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"Raw log file not found at {self.jsonl_path}")

        records = []
        with self.jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                raw = json.loads(line)
                summary = raw.get("summary", {})
                agent = summary.get("agent_name", "unknown")
                model = summary.get("model_identifier", "unknown")
                crashed = summary.get("crashed", False)
                timed_out = summary.get("timed_out", False)
                success = summary.get("success", False)
                reason = summary.get("failure_reason", "")
                steps = summary.get("total_sim_steps", 0)

                # Classify status and acceptance
                if agent == "openai":
                    is_accepted = False
                    if "RateLimitError" in reason:
                        rejection_reason = "openai_quota_exceeded_429"
                        status = "crashed"
                    elif "RuntimeError" in reason:
                        rejection_reason = "openai_runtime_error"
                        status = "crashed"
                    elif steps == 0 and not success:
                        rejection_reason = "openai_zero_step_abort"
                        status = "aborted"
                    else:
                        rejection_reason = "openai_unsupported_harness_crash"
                        status = "crashed" if crashed else "aborted"
                else:
                    # Ollama runs
                    is_accepted = True
                    rejection_reason = ""
                    if crashed:
                        status = "crashed"
                    elif timed_out:
                        status = "timed_out"
                    else:
                        status = "completed"

                record = AttemptAuditRecord(
                    episode_id=summary.get("episode_id", ""),
                    experiment_id=summary.get("experiment_id", ""),
                    recorded_at=summary.get("recorded_at", ""),
                    seed=summary.get("seed"),
                    agent_name=agent,
                    model_identifier=model,
                    fault_type=summary.get("injected_fault_type", "none"),
                    fault_intensity=float(summary.get("fault_intensity", 0.0)),
                    total_sim_steps=steps,
                    total_wall_seconds=float(summary.get("total_wall_seconds", 0.0)),
                    success=success,
                    crashed=crashed,
                    timed_out=timed_out,
                    failure_reason=reason,
                    is_accepted=is_accepted,
                    rejection_reason=rejection_reason,
                    status=status,
                )
                records.append(record)

        self.records = records
        return records

    def summarize(self) -> AccountingSummary:
        if not self.records:
            self.audit()

        total = len(self.records)
        accepted = [r for r in self.records if r.is_accepted]
        rejected = [r for r in self.records if not r.is_accepted]

        all_crashes = sum(1 for r in self.records if r.crashed or r.status == "aborted")
        all_successes = sum(1 for r in self.records if r.success)

        accepted_crashes = sum(1 for r in accepted if r.crashed or r.status == "aborted")
        accepted_successes = sum(1 for r in accepted if r.success)

        rejection_counts = Counter(r.rejection_reason for r in rejected)

        by_agent: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "crashed": 0, "success": 0, "completed": 0, "aborted": 0})
        for r in self.records:
            entry = by_agent[r.agent_name]
            entry["total"] += 1
            if r.crashed:
                entry["crashed"] += 1
            if r.success:
                entry["success"] += 1
            if r.status == "completed":
                entry["completed"] += 1
            if r.status == "aborted":
                entry["aborted"] += 1

        for ag, st in by_agent.items():
            st["crash_rate"] = round(st["crashed"] / st["total"], 4) if st["total"] else 0.0
            st["success_rate"] = round(st["success"] / st["total"], 4) if st["total"] else 0.0

        by_fault: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "success": 0, "crashed": 0})
        for r in accepted:
            entry = by_fault[r.fault_type]
            entry["total"] += 1
            if r.success:
                entry["success"] += 1
            if r.crashed:
                entry["crashed"] += 1
        for ft, st in by_fault.items():
            st["success_rate"] = round(st["success"] / st["total"], 4) if st["total"] else 0.0

        return AccountingSummary(
            total_attempts=total,
            accepted_attempts=len(accepted),
            rejected_attempts=len(rejected),
            all_attempts_crash_rate=round(all_crashes / total, 4) if total else 0.0,
            all_attempts_success_rate=round(all_successes / total, 4) if total else 0.0,
            accepted_crash_rate=round(accepted_crashes / len(accepted), 4) if accepted else 0.0,
            accepted_success_rate=round(accepted_successes / len(accepted), 4) if accepted else 0.0,
            rejection_reasons=dict(rejection_counts),
            by_agent=dict(by_agent),
            by_fault_accepted=dict(by_fault),
        )

    def generate_markdown_report(self) -> str:
        summary = self.summarize()
        lines = [
            "# Episode Attempt Accounting Report",
            "",
            "## 1. Overview",
            f"- **Total Raw Attempts Ingested**: {summary.total_attempts}",
            f"- **Accepted Episodes**: {summary.accepted_attempts} ({summary.accepted_attempts / summary.total_attempts:.1%})",
            f"- **Rejected Attempts**: {summary.rejected_attempts} ({summary.rejected_attempts / summary.total_attempts:.1%})",
            "",
            "## 2. All-Attempts vs. Accepted Reliability",
            "",
            "| Metric | All Attempts (N=169) | Accepted Episodes (N=70) | Impact / Bias |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Crash Rate** | **{summary.all_attempts_crash_rate:.1%}** ({summary.total_attempts - summary.accepted_attempts + int(summary.accepted_crash_rate * summary.accepted_attempts)}/{summary.total_attempts}) | **{summary.accepted_crash_rate:.1%}** (0/{summary.accepted_attempts}) | Discarding OpenAI runs masked a 57%+ abort/crash rate |",
            f"| **Success Rate** | **{summary.all_attempts_success_rate:.1%}** ({int(summary.all_attempts_success_rate * summary.total_attempts)}/{summary.total_attempts}) | **{summary.accepted_success_rate:.1%}** ({int(summary.accepted_success_rate * summary.accepted_attempts)}/{summary.accepted_attempts}) | Paper reported 28.6% by omitting failed client invocations |",
            "",
            "## 3. Discarded Records Breakdown (N=99)",
            "",
            "| Rejection Reason | Count | Root Cause | Defined Timing |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for reason, count in summary.rejection_reasons.items():
            if "quota" in reason:
                root = "OpenAI HTTP 429 quota exhaustion (`insufficient_quota`)"
            elif "runtime" in reason:
                root = "OpenAI client initialization exception / missing key runtime failure"
            elif "abort" in reason:
                root = "Zero-step early invocation termination before simulation started"
            else:
                root = "External API client error"
            lines.append(f"| `{reason}` | {count} | {root} | Post-hoc filtering after failed API execution |")

        lines.extend([
            "",
            "## 4. Per-Agent Breakdown",
            "",
            "| Agent / Runtime | Model | Attempts | Crashes / Aborts | Successes | Crash Rate | Success Rate |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for agent, stats in summary.by_agent.items():
            model = "gpt-4o" if agent == "openai" else "llama3"
            crashes = stats["crashed"] + stats["aborted"]
            lines.append(f"| `{agent}` | `{model}` | {stats['total']} | {crashes} | {stats['success']} | {crashes / stats['total']:.1%} | {stats['success_rate']:.1%} |")

        lines.extend([
            "",
            "## 5. Accepted Episodes by Fault Condition (Ollama / llama3)",
            "",
            "| Fault Type | Episodes | Successes | Success Rate |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for fault, stats in summary.by_fault_accepted.items():
            lines.append(f"| `{fault}` | {stats['total']} | {stats['success']} | {stats['success_rate']:.1%} |")

        lines.extend([
            "",
            "## 6. Discard Rule Evaluation & Scientific Integrity Assessment",
            "- **Rule Definition Timing**: Post-hoc. The 99 runs were attempted with OpenAI; when quota/connection failed, the author switched to Ollama and silently omitted the OpenAI logs.",
            "- **Bias Impact**: Severe if reporting 'agent reliability' or 'system stability', because claiming 0% crash rate is demonstrably false when external API infrastructure fails 100% of the time.",
            "- **Defensible Revision**: In the revised paper, both all-attempt (infrastructure reliability) and accepted-cohort (planner execution given complete environment connection) must be reported side-by-side with full transparency.",
        ])
        return "\n".join(lines)


def main() -> None:
    auditor = AttemptAccountingAuditor()
    records = auditor.audit()
    print(f"Audited {len(records)} records from {auditor.jsonl_path}")
    summary = auditor.summarize()
    print(f"Accepted: {summary.accepted_attempts}, Rejected: {summary.rejected_attempts}")
    print(f"All attempts crash rate: {summary.all_attempts_crash_rate:.1%}")
    print(f"Accepted crash rate: {summary.accepted_crash_rate:.1%}")

    report_path = Path("artifacts/accounting_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(auditor.generate_markdown_report(), encoding="utf-8")
    print(f"Wrote accounting report to {report_path}")

    json_path = Path("artifacts/accounting_report.json")
    json_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
    print(f"Wrote accounting summary JSON to {json_path}")


if __name__ == "__main__":
    main()
