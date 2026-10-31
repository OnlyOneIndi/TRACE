
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import (
    save_verification_audit,
    load_verification_audit,
)


with TemporaryDirectory() as folder:

    report_path = (
        Path(folder) / "trace_report_test.json"
    )

    report_path.write_text(
        '{"topic": "Robotic Navigation"}',
        encoding="utf-8",
    )

    checks = {
        "research_constraints": True,
        "source_metadata": True,
        "evidence_quotations": True,
        "numerical_consistency": True,
    }

    audit_path = save_verification_audit(
        report_path=report_path,
        retrieved_papers=[
            {
                "url": "https://openalex.org/W123"
            }
        ],
        max_papers=3,
        from_year=2023,
        checks=checks,
    )

    assert audit_path.exists()

    audit = load_verification_audit(
        report_path
    )

    assert audit["status"] == "passed"
    assert audit["report_unchanged"] is True
    assert len(audit["retrieved_source_urls"]) == 1

    # Simulate someone modifying a saved report.
    report_path.write_text(
        '{"topic": "Modified Research"}',
        encoding="utf-8",
    )

    modified_audit = load_verification_audit(
        report_path
    )

    assert modified_audit["report_unchanged"] is False

    print("ALL AUDIT TESTS PASSED")
