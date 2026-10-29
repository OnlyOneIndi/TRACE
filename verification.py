import re
from decimal import Decimal
from schemas import ResearchReport


def verify_report(
    report: ResearchReport,
    source_papers: list[dict]
) -> list[str]:
    """Verify report metadata against OpenAlex records."""

    errors = []

    # Reject empty reports
    if not report.papers:
        errors.append(
            "The generated report contains no research papers."
        )
        return errors

    # Index the retrieved papers by URL
    sources_by_url = {
        paper["url"]: paper
        for paper in source_papers
    }

    # Track papers we have already encountered
    seen_urls = set()

    for paper in report.papers:

        # Reject duplicate paper URLs
        if paper.url in seen_urls:
            errors.append(
                f"Duplicate paper detected: {paper.title}"
            )
            continue

        seen_urls.add(paper.url)

        # Find the matching original record
        source = sources_by_url.get(paper.url)

        if source is None:
            errors.append(
                f"Paper not found in retrieved sources: {paper.title}"
            )
            continue

        # Compare paper metadata
        if paper.title != source["title"]:
            errors.append(
                f"Title mismatch: {paper.url}"
            )

        if paper.year != source["year"]:
            errors.append(
                f"Year mismatch: {paper.title}"
            )

        if paper.citations != source["citations"]:
            errors.append(
                f"Citation count mismatch: {paper.title}"
            )

    return errors


def verify_evidence(
    report: ResearchReport,
    source_papers: list[dict]
) -> list[str]:
    """Check evidence passages against retrieved abstracts."""

    errors = []

    # Index sources by their OpenAlex URLs
    sources_by_url = {
        paper["url"]: paper
        for paper in source_papers
    }

    for finding in report.key_findings:

        # Check that the referenced source exists
        source = sources_by_url.get(finding.source_url)

        if source is None:
            errors.append(
                f"Unknown source URL: {finding.source_url}"
            )
            continue

        # Retrieve the source abstract
        abstract = source.get("abstract")

        if not abstract:
            errors.append(
                f"No abstract available: {finding.source_url}"
            )
            continue

        # Normalize whitespace and capitalization
        normalized_abstract = " ".join(
            abstract.split()
        ).casefold()

        normalized_evidence = " ".join(
            finding.evidence.split()
        ).casefold()

        # Check whether the evidence exists in the abstract
        if (
            not normalized_evidence
            or normalized_evidence not in normalized_abstract
        ):
            errors.append(
                f"Evidence not found in abstract: {finding.source_url}"
            )

    return errors


def extract_percentages(text: str) -> set[Decimal]:
    """Extract percentage values from text."""

    pattern = r"(?<![\w.])(\d+(?:\.\d+)?)\s*%"

    matches = re.findall(pattern, text)

    return {
        Decimal(value)
        for value in matches
    }


def check_numerical_consistency(
    report: ResearchReport
) -> list[str]:
    """Flag percentages in claims missing from their evidence."""

    warnings = []

    for finding in report.key_findings:
        claim_values = extract_percentages(finding.claim)
        evidence_values = extract_percentages(finding.evidence)

        unsupported_values = claim_values - evidence_values

        if unsupported_values:
            warnings.append(
                f"Percentage mismatch in {finding.source_url}: "
                f"Claim contains {sorted(claim_values)}, "
                f"evidence contains {sorted(evidence_values)}"
            )

    return warnings

