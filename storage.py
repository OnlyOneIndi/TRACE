
from pathlib import Path
from datetime import datetime, timezone

from schemas import ResearchReport


# Directory containing saved research reports
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def save_report(report: ResearchReport) -> Path:
    """Save a verified research report as JSON."""

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


def list_saved_reports() -> list[Path]:
    """Return previously saved reports, newest first."""

    if not REPORTS_DIR.exists():
        return []

    reports = list(
        REPORTS_DIR.glob("trace_report_*.json")
    )

    return sorted(
        reports,
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )


def load_report(filepath: Path) -> ResearchReport:
    """Load and validate a previously saved report."""

    filepath = Path(filepath).resolve()

    reports_directory = REPORTS_DIR.resolve()

    if filepath.parent != reports_directory:
        raise ValueError(
            "Report is outside the reports directory."
        )

    if filepath.suffix.lower() != ".json":
        raise ValueError(
            "Only JSON research reports can be loaded."
        )

    content = filepath.read_text(
        encoding="utf-8"
    )

    return ResearchReport.model_validate_json(
        content
    )
