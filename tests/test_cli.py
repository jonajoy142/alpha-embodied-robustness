"""
Unit tests for Alpha CLI commands.
"""

from pathlib import Path
from alpha.cli import main


def test_cli_report_generation(tmp_path):
    """alpha report should generate a valid HTML report."""
    report_file = tmp_path / "test_report.html"
    exit_code = main(["report", "--output", str(report_file)])
    assert exit_code == 0
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "Alpha: Systematic Fault Injection" in content
    assert "TOST Equivalence Test" in content

