
import os
import requests

from pathlib import Path
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


load_dotenv()

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "google:gemini-3.5-flash-lite"
)


class ResearchVerificationError(Exception):
    """Raised when a research report fails verification."""


def run_research(question: str) -> tuple[ResearchReport, Path]:
    """Run research, verify the report, and save it."""

    if not question.strip():
        raise ValueError("Research question cannot be empty.")

    # Records are local to this research run
    retrieved_papers = []
    search_failed = False

    agent = Agent(
        MODEL_NAME,
        output_type=ResearchReport,
        instructions=(
            "You are Trace, a scientific research assistant. "
            "Always use search_openalex to retrieve research papers. "
            "Use only the papers returned by the tool. "
            "Preserve titles, years, URLs, and citation counts exactly. "
            "Summarize papers using their retrieved abstracts. "
            "Every key finding must have a claim, an exact verbatim "
            "evidence passage from an abstract, and its source URL. "
            "Do not paraphrase or invent evidence passages. "
            "Keep numerical values consistent with the evidence. "
            "Do not invent research papers or citations. "
            "If no reliable evidence is available, explain the "
            "limitation rather than fabricating results."
        ),
    )

    @agent.tool_plain
    def search_openalex(
        query: str,
        max_results: int = 3,
        from_year: int | None = None,
    ) -> list[dict]:
        """Search OpenAlex for academic research papers.

        Args:
            query: Research topic or search keywords.
            max_results: Number of results, from 1 to 10.
            from_year: Optional earliest publication year.
        """
        nonlocal search_failed

        try:
            papers = search_papers(
                query=query,
                max_results=max_results,
                from_year=from_year,
            )

            retrieved_papers.extend(papers)
            return papers

        except (requests.exceptions.RequestException, ValueError) as error:
            search_failed = True
            return [{"error": str(error)}]

    # Execute the language-model research workflow
    result = agent.run_sync(question)
    report = result.output

    # Stop if retrieval failed
    if search_failed or not retrieved_papers:
        raise ResearchVerificationError(
            "No reliable OpenAlex records were retrieved."
        )

    # Check metadata
    metadata_errors = verify_report(
        report=report,
        source_papers=retrieved_papers,
    )

    # Check whether cited evidence exists
    evidence_errors = verify_evidence(
        report=report,
        source_papers=retrieved_papers,
    )

    if not report.key_findings:
        evidence_errors.append(
            "No evidence-backed findings were provided."
        )

    # Check percentages in claims against evidence
    numerical_warnings = check_numerical_consistency(
        report=report
    )

    problems = (
        metadata_errors
        + evidence_errors
        + numerical_warnings
    )

    if problems:
        raise ResearchVerificationError(
            "\n".join(problems)
        )

    # Save only after all implemented checks pass
    saved_path = save_report(report)

    return report, saved_path
