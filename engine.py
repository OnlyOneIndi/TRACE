
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
from audit import save_verification_audit


# ─────────────────────────────────────────
# ENVIRONMENT CONFIGURATION
# ─────────────────────────────────────────

load_dotenv()

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "google:gemini-3.5-flash-lite"
)


# ─────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────

class ResearchVerificationError(Exception):
    """Raised when a report fails verification."""
    pass


# ─────────────────────────────────────────
# MAIN RESEARCH ENGINE
# ─────────────────────────────────────────

def run_research(
    question: str,
    max_papers: int = 3,
    from_year: int | None = None,
) -> tuple[ResearchReport, Path]:
    """
    Run Trace's complete research workflow.

    Workflow:
        1. Validate research settings.
        2. Initialize Gemini.
        3. Search OpenAlex.
        4. Generate a structured report.
        5. Restore authoritative source metadata.
        6. Enforce research constraints.
        7. Verify metadata and evidence.
        8. Check numerical consistency.
        9. Save the verified report.
       10. Create a verification audit.
       11. Return the report and file path.
    """

    # ─────────────────────────────────────
    # 1. VALIDATE RESEARCH INPUT
    # ─────────────────────────────────────

    question = question.strip()

    if not question:
        raise ValueError(
            "Research question cannot be empty."
        )

    if not isinstance(max_papers, int):
        raise ValueError(
            "Maximum papers must be an integer."
        )

    if not 1 <= max_papers <= 10:
        raise ValueError(
            "Maximum papers must be between 1 and 10."
        )

    current_year = datetime.now().year

    if from_year is not None:
        if (
            not isinstance(from_year, int)
            or not 1900 <= from_year <= current_year
        ):
            raise ValueError(
                "Invalid earliest publication year."
            )

    user_max_papers = max_papers
    user_from_year = from_year

    retrieved_papers = []
    search_failed = False

    # ─────────────────────────────────────
    # 2. INITIALIZE GEMINI AGENT
    # ─────────────────────────────────────

    agent = Agent(
        MODEL_NAME,
        output_type=ResearchReport,
        instructions=(
            "You are Trace, a scientific research assistant. "

            "Always use search_openalex before generating "
            "a research report. "

            "Use only academic papers returned by the tool. "

            "Preserve the exact source URLs returned "
            "by OpenAlex. "

            "Do not invent research paper titles, "
            "publication years, citation counts, "
            "or references. "

            "Summarize each paper based on its "
            "retrieved abstract. "

            "For every key finding, provide a claim, "
            "an evidence passage, and a source URL. "

            "Every evidence passage must be copied "
            "verbatim from a retrieved paper abstract. "

            "Do not paraphrase, alter, or fabricate "
            "evidence passages. "

            "Associate each finding with the correct "
            "source paper URL. "

            "Ensure claims are consistent with "
            "the supporting evidence. "

            "Keep numerical values consistent with "
            "the evidence passages. "

            "Do not invent evidence for papers "
            "that have no abstracts. "

            "Respect the user's maximum paper count "
            "and earliest publication-year settings. "

            "If reliable evidence is unavailable, "
            "do not fabricate a research conclusion."
        ),
    )

    # ─────────────────────────────────────
    # 3. REGISTER OPENALEX TOOL
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
            max_results: Model-suggested paper count.
            from_year: Model-suggested earliest year.
        """

        nonlocal search_failed

        # User settings take priority.
        effective_max = user_max_papers

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

            return [
                {
                    "error": str(error)
                }
            ]

    # ─────────────────────────────────────
    # 4. EXECUTE RESEARCH
    # ─────────────────────────────────────

    configured_question = (
        f"{question}\n\n"
        "Research configuration:\n"
        f"- Maximum papers in final report: "
        f"{user_max_papers}\n"
        f"- Earliest publication year: "
        f"{user_from_year if user_from_year is not None else 'Not specified'}\n"
        "Use only the retrieved academic papers."
    )

    result = agent.run_sync(
        configured_question
    )

    report = result.output

    # ─────────────────────────────────────
    # 5. CHECK RETRIEVED SOURCES
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
            # Unknown source URLs will still
            # fail metadata verification.
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
            f"Report contains {len(report.papers)} "
            f"papers, but the maximum is "
            f"{user_max_papers}."
        )

    if user_from_year is not None:

        for paper in report.papers:

            original = sources_by_url.get(
                paper.url
            )

            if original is None:
                continue

            if (
                original["year"] is None
                or original["year"] < user_from_year
            ):

                constraint_errors.append(
                    f"Paper does not meet the "
                    f"{user_from_year}+ requirement: "
                    f"{paper.title}"
                )

    # ─────────────────────────────────────
    # 8. VERIFY SOURCE METADATA
    # ─────────────────────────────────────

    metadata_errors = verify_report(
        report=report,
        source_papers=retrieved_papers,
    )

    # ─────────────────────────────────────
    # 9. VERIFY EVIDENCE PASSAGES
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

    numerical_warnings = (
        check_numerical_consistency(report)
    )

    # ─────────────────────────────────────
    # 11. EVALUATE VERIFICATION RESULTS
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

    # Record exactly which checks passed.
    checks = {
        "research_constraints": (
            len(constraint_errors) == 0
        ),
        "source_metadata": (
            len(metadata_errors) == 0
        ),
        "evidence_quotations": (
            len(evidence_errors) == 0
        ),
        "numerical_consistency": (
            len(numerical_warnings) == 0
        ),
    }

    # ─────────────────────────────────────
    # 12. SAVE VERIFIED REPORT
    # ─────────────────────────────────────

    saved_path = save_report(report)

    # ─────────────────────────────────────
    # 13. SAVE VERIFICATION AUDIT
    # ─────────────────────────────────────

    try:

        save_verification_audit(
            report_path=saved_path,
            retrieved_papers=retrieved_papers,
            max_papers=user_max_papers,
            from_year=user_from_year,
            checks=checks,
        )

    except Exception as error:

        # Keep the report and audit consistent:
        # if the audit cannot be created, remove
        # the newly generated report.
        saved_path.unlink(missing_ok=True)

        raise RuntimeError(
            "Report passed verification, but its "
            "audit record could not be saved. "
            "The newly saved report was removed."
        ) from error

    # ─────────────────────────────────────
    # 14. RETURN VERIFIED RESULTS
    # ─────────────────────────────────────

    return report, saved_path
