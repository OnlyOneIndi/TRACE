import hashlib
import json

from datetime import datetime, timezone
from pathlib import Path


AUDIT_VERSION = 1


def save_verification_audit(
    report_path: Path,
    retrieved_papers: list[dict],
    max_papers: int,
    from_year: int | None,
    checks: dict[str, bool],
) -> Path:
    """
    Save the verification audit for an accepted report.

    Must be called only after the research engine has
    completed its checks successfully.
    """

    if not checks or not all(checks.values()):
        raise ValueError(
            "Cannot record a passing audit when checks "
            "are missing or have failed."
        )

    report_path = Path(report_path)

    # Calculate a fingerprint of the saved report.
    report_bytes = report_path.read_bytes()

    report_hash = hashlib.sha256(
        report_bytes
    ).hexdigest()

    # Separate URLs provide a compact record
    # of the source set used during research.
    source_urls = sorted({
        paper["url"]
        for paper in retrieved_papers
    })

    audit = {
        "audit_version": AUDIT_VERSION,
        "verified_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "report_filename": report_path.name,
        "report_sha256": report_hash,
        "status": "passed",
        "checks": checks,
        "research_settings": {
            "max_papers": max_papers,
            "from_year": from_year,
        },
        "retrieved_source_urls": source_urls,
        "limitations": [
            "Metadata was checked against OpenAlex "
            "records retrieved during this run.",
            "Evidence text was checked for inclusion "
            "in retrieved abstracts.",
            "Numerical checks cover percentages, "
            "not every type of numerical claim.",
            "Semantic correctness of research claims "
            "was not independently established.",
        ],
    }

    audit_path = report_path.with_suffix(
        ".audit.json"
    )

    audit_path.write_text(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return audit_path


def load_verification_audit(
    report_path: Path,
) -> dict | None:
    """
    Read an existing audit record.

    Returns None for older reports that have no audit.

    Checks whether the report still matches the
    fingerprint stored in its audit record.
    """

    report_path = Path(report_path)
    audit_path = report_path.with_suffix(
        ".audit.json"
    )

    if not audit_path.exists():
        return None

    audit = json.loads(
        audit_path.read_text(encoding="utf-8")
    )

    actual_hash = hashlib.sha256(
        report_path.read_bytes()
    ).hexdigest()

    audit["report_unchanged"] = (
        actual_hash == audit.get("report_sha256")
    )

    return audit
