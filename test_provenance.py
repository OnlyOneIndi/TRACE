
from schemas import (
    ResearchReport,
    ResearchPaper,
    ResearchFinding,
)

from provenance import build_provenance


report = ResearchReport(
    topic="Robotic Navigation",
    papers=[
        ResearchPaper(
            title="Example Navigation Paper",
            year=2024,
            url="https://openalex.org/W123",
            citations=10,
            summary="A sample summary.",
        )
    ],
    key_findings=[
        ResearchFinding(
            claim="A sample claim.",
            evidence="An example evidence passage.",
            source_url="https://openalex.org/W123",
        )
    ],
    overall_summary="An example report.",
)

records = build_provenance(report)

assert len(records) == 1
assert records[0]["source_linked"] is True
assert records[0]["source_title"] == "Example Navigation Paper"

print("PROVENANCE TEST PASSED")
