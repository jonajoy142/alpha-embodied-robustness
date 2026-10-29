"""
Pre-registered Equivalence Testing Service (TOST) for Alpha.

Implements Two One-Sided Tests (TOST) for paired binary performance data
(Scripted Oracle vs. LLM Planner under matched experimental seeds).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class TOSTResult:
    """Results of Two One-Sided Tests (TOST) for equivalence."""
    sample_size: int
    oracle_successes: int
    llm_successes: int
    oracle_rate: float
    llm_rate: float
    risk_difference: float
    standard_error: float
    margin: float
    alpha: float
    confidence_interval: tuple[float, float]
    z1: float
    p1: float
    z2: float
    p2: float
    p_tost: float
    is_equivalent: bool

    def summary(self) -> str:
        ci_pct = int((1 - 2 * self.alpha) * 100)
        equiv_str = "EQUIVALENT" if self.is_equivalent else "NOT EQUIVALENT"
        return (
            f"TOST Equivalence Test (margin=±{self.margin:.2f}, alpha={self.alpha:.2f}):\n"
            f"  Oracle Success: {self.oracle_rate:.1%} ({self.oracle_successes}/{self.sample_size})\n"
            f"  LLM Success:    {self.llm_rate:.1%} ({self.llm_successes}/{self.sample_size})\n"
            f"  Risk Diff (Δ):  {self.risk_difference:+.3f} (SE = {self.standard_error:.3f})\n"
            f"  {ci_pct}% CI for Δ:   [{self.confidence_interval[0]:+.3f}, {self.confidence_interval[1]:+.3f}]\n"
            f"  TOST p-value:   {self.p_tost:.4e}\n"
            f"  Verdict:        {equiv_str} within margin [-{self.margin:.2f}, +{self.margin:.2f}]"
        )


def _normal_cdf(x: float) -> float:
    """Cumulative distribution function for standard normal distribution."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def tost_paired_equivalence_test(
    oracle_results: Sequence[bool],
    llm_results: Sequence[bool],
    margin: float = 0.15,
    alpha: float = 0.05,
) -> TOSTResult:
    """
    Execute TOST for paired binary data.

    Parameters
    ----------
    oracle_results:
        Sequence of booleans indicating success for Oracle under matched seeds.
    llm_results:
        Sequence of booleans indicating success for LLM under matched seeds.
    margin:
        Pre-registered equivalence bound delta (default 0.15 = 15 percentage points).
    alpha:
        Significance level per one-sided test (default 0.05 for 90% CI).
    """
    if len(oracle_results) != len(llm_results):
        raise ValueError(f"Matched lengths required: {len(oracle_results)} != {len(llm_results)}")

    n = len(oracle_results)
    if n == 0:
        raise ValueError("Cannot perform TOST on empty sequences.")

    # Contingency counts
    a = sum(1 for o, l in zip(oracle_results, llm_results) if o and l)      # (1, 1)
    b = sum(1 for o, l in zip(oracle_results, llm_results) if o and not l)  # (1, 0) discordant
    c = sum(1 for o, l in zip(oracle_results, llm_results) if not o and l)  # (0, 1) discordant
    d = sum(1 for o, l in zip(oracle_results, llm_results) if not o and not l) # (0, 0)

    oracle_successes = a + b
    llm_successes = a + c
    p_oracle = oracle_successes / n
    p_llm = llm_successes / n
    diff = p_oracle - p_llm  # = (b - c) / n

    # Standard error for paired difference of proportions
    variance = (b + c - ((b - c) ** 2) / n) / (n * n)
    se = math.sqrt(max(variance, 1e-12))

    # Critical z for one-sided test (e.g. z=1.645 for alpha=0.05, 90% CI)
    # Using inverse erf for exact z:
    # 1 - alpha = _normal_cdf(z_crit) => erf(z_crit / sqrt(2)) = 1 - 2*alpha
    z_crit = math.sqrt(2.0) * _erf_inverse(1.0 - 2.0 * alpha)
    ci_lower = diff - z_crit * se
    ci_upper = diff + z_crit * se

    # Test 1: H0_1: diff <= -margin vs H1_1: diff > -margin
    z1 = (diff - (-margin)) / se
    p1 = 1.0 - _normal_cdf(z1)

    # Test 2: H0_2: diff >= margin vs H1_2: diff < margin
    z2 = (margin - diff) / se
    p2 = 1.0 - _normal_cdf(z2)

    p_tost = max(p1, p2)
    is_equivalent = bool(ci_lower > -margin and ci_upper < margin)

    return TOSTResult(
        sample_size=n,
        oracle_successes=oracle_successes,
        llm_successes=llm_successes,
        oracle_rate=p_oracle,
        llm_rate=p_llm,
        risk_difference=diff,
        standard_error=se,
        margin=margin,
        alpha=alpha,
        confidence_interval=(ci_lower, ci_upper),
        z1=z1,
        p1=p1,
        z2=z2,
        p2=p2,
        p_tost=p_tost,
        is_equivalent=is_equivalent,
    )


def _erf_inverse(x: float) -> float:
    """Winitzki approximation for inverse error function."""
    a = 0.147
    sgn = 1.0 if x >= 0 else -1.0
    term1 = 2.0 / (math.pi * a) + math.log(1.0 - x * x) / 2.0
    term2 = math.log(1.0 - x * x) / a
    val = term1 * term1 - term2
    return sgn * math.sqrt(math.sqrt(max(0.0, val)) - term1)

