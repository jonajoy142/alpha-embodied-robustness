.PHONY: help test gates calibrate audit experiment analyze all clean

PYTHON := python3
export PYTHONPATH := src

help:
	@echo "Alpha Chaos Harness Makefile"
	@echo "----------------------------"
	@echo "  make test        - Run all unit and regression tests"
	@echo "  make gates       - Execute Pilot Gates G1-G8"
	@echo "  make calibrate   - Calibrate fault intensity parameters"
	@echo "  make audit       - Audit raw episode attempts (169 records)"
	@echo "  make experiment  - Run sample experiment matrix"
	@echo "  make analyze     - Generate tables, figures, and summaries"
	@echo "  make all         - Run test, gates, calibrate, audit, analyze"
	@echo "  make clean       - Remove cached pyc, pytest files"

test:
	$(PYTHON) -m pytest tests/ -v

gates:
	$(PYTHON) scripts/run_pilot_gates.py

calibrate:
	$(PYTHON) scripts/calibrate_fault_intensities.py

audit:
	$(PYTHON) -m alpha.services.attempt_accounting

experiment:
	$(PYTHON) scripts/run_experiment_matrix.py --agent scripted_oracle --control-runs 2 --episodes-per-variation 1 --concurrent-runs 1

analyze:
	$(PYTHON) scripts/analyze_experiments.py

all: calibrate audit test gates analyze

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
