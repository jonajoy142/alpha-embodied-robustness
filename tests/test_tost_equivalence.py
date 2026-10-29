"""
Unit tests for pre-registered TOST Equivalence Testing.
"""

from alpha.services.equivalence_testing import tost_paired_equivalence_test


def test_tost_identical_outcomes_declared_equivalent():
    """Identical outcomes across planners should be formally declared equivalent."""
    # 60 episodes, 33 successes each, zero discordant pairs
    oracle = [True] * 33 + [False] * 27
    llm = [True] * 33 + [False] * 27

    res = tost_paired_equivalence_test(oracle, llm, margin=0.15, alpha=0.05)

    assert res.risk_difference == 0.0
    assert res.is_equivalent is True
    assert res.p_tost < 0.01
    assert res.confidence_interval[0] > -0.15
    assert res.confidence_interval[1] < 0.15


def test_tost_divergent_outcomes_declared_not_equivalent():
    """Large performance divergence outside the margin should reject equivalence."""
    # Oracle: 100% success (15/15), LLM: 0% success (0/15)
    oracle = [True] * 15
    llm = [False] * 15

    res = tost_paired_equivalence_test(oracle, llm, margin=0.15, alpha=0.05)

    assert res.risk_difference == 1.0
    assert res.is_equivalent is False
    assert res.confidence_interval[0] > 0.15

