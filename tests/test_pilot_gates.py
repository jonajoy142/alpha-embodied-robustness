import pytest
from alpha.services.pilot_gates import PilotGateRunner


def test_pilot_gates_g1_to_g8():
    runner = PilotGateRunner()
    results = runner.run_all_gates()
    assert len(results) == 8
    for r in results:
        assert r.passed, f"Gate {r.gate_id} ({r.name}) failed: {r.details}"
