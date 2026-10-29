import pytest
from alpha.services.attempt_accounting import AttemptAccountingAuditor


def test_attempt_accounting_audit():
    auditor = AttemptAccountingAuditor("data/raw/pilot/phase_a_pilot/episodes.jsonl")
    records = auditor.audit()
    assert len(records) == 169

    accepted = [r for r in records if r.is_accepted]
    rejected = [r for r in records if not r.is_accepted]

    assert len(accepted) == 70
    assert len(rejected) == 99

    summary = auditor.summarize()
    assert summary.total_attempts == 169
    assert summary.accepted_attempts == 70
    assert summary.rejected_attempts == 99
    assert summary.accepted_crash_rate == 0.0
    assert summary.all_attempts_crash_rate > 0.50

    # Verify breakdown of rejected attempts
    assert "openai_runtime_error" in summary.rejection_reasons
    assert "openai_quota_exceeded_429" in summary.rejection_reasons

    # Check report generation
    report = auditor.generate_markdown_report()
    assert "Episode Attempt Accounting Report" in report
    assert "N=169" in report
    assert "N=70" in report
