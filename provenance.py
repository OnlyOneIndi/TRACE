
from schemas import ResearchReport


def build_provenance(report: ResearchReport) -> list[dict]:
    """
    Connect each generated finding to its cited paper.

    This function checks source relationships.
    It does not independently validate scientific claims.
    """

    papers_by_url = {
        paper.url: paper
        for paper in report.papers
    }

    provenance_records = []

    for index, finding in enumerate(
        report.key_findings,
        start=1
    ):
        source_paper = papers_by_url.get(
            finding.source_url
        )

        record = {
            "finding_number": index,
            "claim": finding.claim,
            "evidence": finding.evidence,
            "source_url": finding.source_url,
            "source_linked": source_paper is not None,
            "source_title": None,
            "source_year": None,
            "source_citations": None,
        }

        if source_paper is not None:
            record["source_title"] = source_paper.title
            record["source_year"] = source_paper.year
            record["source_citations"] = (
                source_paper.citations
            )

        provenance_records.append(record)

    return provenance_records
