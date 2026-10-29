#!/usr/bin/env python3
"""
Run all pilot gates (G1–G8) and report PASS/FAIL.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from alpha.services.pilot_gates import PilotGateRunner


def main() -> None:
    runner = PilotGateRunner()
    results = runner.run_all_gates()
    report = runner.generate_report()
    print(report)

    out_md = Path("artifacts/pilot_gate_report.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(report, encoding="utf-8")
    print(f"\nWrote gate report to {out_md}")

    out_json = Path("artifacts/pilot_gate_report.json")
    out_json.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    print(f"Wrote gate JSON to {out_json}")

    all_passed = all(r.passed for r in results)
    if not all_passed:
        print("\nERROR: One or more pilot gates failed!")
        sys.exit(1)
    else:
        print("\nSUCCESS: All pilot gates passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
