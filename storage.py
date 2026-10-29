
from pathlib import Path
from datetime import datetime, timezone

from schemas import ResearchReport


REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def save_report(report: ResearchReport) -> Path:
    """Save a validated research report as JSON."""

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    filename = f"trace_report_{timestamp}.json"

    filepath = REPORTS_DIR / filename

    filepath.write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8"
    )

    return filepath
