
import os
import requests

from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from pydantic_ai import Agent

from research import search_papers
from schemas import ResearchReport
from verification import (
    verify_report,
    verify_evidence,
    check_numerical_consistency,
)
from storage import save_report


# ─────────────────────────────────────────
# ENVIRONMENT CONFIGURATION
# ─────────────────────────────────────────

load_dotenv()

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "google:gemini-3.5-flash-lite"
)


# ─────────────────────────────────────────
# CUSTOM ERROR
# ─────────────────────────────────────────

class ResearchVerificationError(Exception):
    """Raised when a report fails verification."""
    pass


# ─────────────────────────────────────────
# RESEARCH ENGINE
# ─────────────────────────────────────────

def run_research(
    question: str,
    max_papers: int = 3,
    from_year: int | None = None,
) -> tuple[ResearchReport, Path]:
    """
    Run the complete Trace research workflow.

    Args:
        question:
            User's research question.

        max_papers:
            Maximum papers allowed in each search
            and in the final report.

        from_year:
            Optional minimum publication year.

    Returns:
        Validated research report and saved file path.
    """

    # ─────────────────────────────────────
    # 1. VALIDATE USER INPUT
    # ─────────────────────────────────────

    question = question.strip()

    if not question:
        raise ValueError(
            "Research question cannot be empty."
        )

    if not 1 <= max_papers <= 10:
        raise ValueError(
            "Maximum papers must be between 1 and 10."
        )

    current_year = datetime.now().year

    if from_year is not None:
        if not 1900 <= from_year <= current_year:
            raise ValueError(
                "Invalid earliest publication year."
            )

    # Preserve user settings separately from
    # arguments the model may pass to the tool.
    user_max_papers = max_papers
    user_from_year = from_year

    retrieved_papers = []
    search_failed = False

    # ─────────────────────────────────────
    # 2. INITIALIZE RESEARCH AGENT
    # ─────────────────────────────────────

    agent = Agent(
        MODEL_NAME,
        output_type=ResearchReport,
        instructions=(
            "You are Trace, a scientific research assistant. "

            "Always use search_openalex before generating "
            "a research report. "

            "Use only academic papers returned by the tool. "

            "Preserve original source URLs exactly. "

            "Do not invent titles, years, citation counts, "
            "or academic references. "

            "Summarize each paper using its abstract. "

            "For every key finding, provide a claim, "
            "an evidence passage, and the source URL. "

            "Evidence passages must be copied verbatim "
            "from the retrieved abstracts. "

            "Do not paraphrase the evidence passages. "

            "Claims must be consistent with the "
            "supporting evidence. "

            "Keep numerical values consistent with evidence. "

            "Do not invent results when evidence is missing. "

            "The research tool applies the user's maximum "
            "paper count and publication-year settings. "

            "Do not include papers outside those constraints."
        ),
    )

    # ─────────────────────────────────────
    # 3. OPENALEX SEARCH TOOL
    # ─────────────────────────────────────

    @agent.tool_plain
    def search_openalex(
        query: str,
        max_results: int = 3,
        from_year: int | None = None,
    ) -> list[dict]:
        """
        Search OpenAlex for academic papers.

        Args:
            query: Search keywords.
            max_results: Suggested number of papers.
            from_year: Suggested earliest publication year.
        """

        nonlocal search_failed

        # The user controls the maximum.
        effective_max = user_max_papers

        # Explicit user year takes priority.
        # Otherwise, the model can suggest one.
        effective_year = (
            user_from_year
            if user_from_year is not None
            else from_year
        )

        try:
            papers = search_papers(
                query=query,
                max_results=effective_max,
                from_year=effective_year,
            )

            retrieved_papers.extend(papers)

            return papers

        except (
            requests.exceptions.RequestException,
            ValueError,
        ) as error:

            search_failed = True

            return [{"error": str(error)}]

    # ─────────────────────────────────────
    # 4. RUN RESEARCH
    # ─────────────────────────────────────

    result = agent.run_sync(
        (
            f"{question}\n\n"
            f"Research configuration:\n"
            f"- Maximum papers in final report: "
            f"{user_max_papers}\n"
            f"- Earliest publication year: "
            f"{user_from_year if user_from_year is not None else 'Not specified'}\n"
            "Use only retrieved academic sources."
        )
    )

    report = result.output

    # ─────────────────────────────────────
    # 5. CHECK RETRIEVAL
    # ─────────────────────────────────────

    if search_failed or not retrieved_papers:
        raise ResearchVerificationError(
            "No reliable OpenAlex records were retrieved."
        )

    # ─────────────────────────────────────
    # 6. RESTORE AUTHORITATIVE METADATA
    # ─────────────────────────────────────

    sources_by_url = {
        paper["url"]: paper
        for paper in retrieved_papers
    }

    for paper in report.papers:

        original = sources_by_url.get(
            paper.url
        )

        if original is None:
            # Unknown URLs must fail verification.
            continue

        paper.title = original["title"]
        paper.year = original["year"]
        paper.citations = original["citations"]

    # ─────────────────────────────────────
    # 7. ENFORCE RESEARCH CONSTRAINTS
    # ─────────────────────────────────────

    constraint_errors = []

    if len(report.papers) > user_max_papers:
        constraint_errors.append(
            f"Report contains {len(report.papers)} papers, "
            f"but the maximum is {user_max_papers}."
        )

    if user_from_year is not None:

        for paper in report.papers:

            # Check only matching source records.
            original = sources_by_url.get(paper.url)

            if original is None:
                continue

            if (
                original["year"] is None
                or original["year"] < user_from_year
            ):
                constraint_errors.append(
                    f"Paper does not meet the "
                    f"{user_from_year}+ year requirement: "
                    f"{paper.title}"
                )

    # ─────────────────────────────────────
    # 8. VERIFY PAPER METADATA
    # ─────────────────────────────────────

    metadata_errors = verify_report(
        report=report,
        source_papers=retrieved_papers,
    )

    # ─────────────────────────────────────
    # 9. VERIFY EVIDENCE
    # ─────────────────────────────────────

    evidence_errors = verify_evidence(
        report=report,
        source_papers=retrieved_papers,
    )

    if not report.key_findings:
        evidence_errors.append(
            "No evidence-backed findings were provided."
        )

    # ─────────────────────────────────────
    # 10. CHECK NUMERICAL CONSISTENCY
    # ─────────────────────────────────────

    numerical_warnings = check_numerical_consistency(
        report=report
    )

    # ─────────────────────────────────────
    # 11. COLLECT VERIFICATION PROBLEMS
    # ─────────────────────────────────────

    problems = (
        constraint_errors
        + metadata_errors
        + evidence_errors
        + numerical_warnings
    )

    if problems:
        raise ResearchVerificationError(
            "\n".join(problems)
        )

    # ─────────────────────────────────────
    # 12. SAVE VERIFIED REPORT
    # ─────────────────────────────────────

    saved_path = save_report(report)

    return report, saved_path
