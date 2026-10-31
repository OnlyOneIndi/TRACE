
from dataclasses import dataclass, field

from executor import ExecutionResult
from schemas import ResearchReport


# ─────────────────────────────────────────
# COVERAGE DATA STRUCTURES
# ─────────────────────────────────────────

@dataclass
class TaskCoverage:
    title: str
    query: str
    execution_status: str
    coverage_status: str

    retrieved_papers: int = 0
    included_papers: int = 0
    findings_linked: int = 0

    notes: list[str] = field(default_factory=list)


@dataclass
class CoverageResult:
    objective: str
    tasks: list[TaskCoverage]

    @property
    def total_tasks(self) -> int:
        return len(self.tasks)

    @property
    def evidence_linked_tasks(self) -> int:
        return sum(
            task.coverage_status == "evidence_linked"
            for task in self.tasks
        )

    @property
    def incomplete_tasks(self) -> list[TaskCoverage]:
        return [
            task for task in self.tasks
            if task.coverage_status != "evidence_linked"
        ]


# ─────────────────────────────────────────
# COVERAGE ANALYZER
# ─────────────────────────────────────────

def assess_research_coverage(
    execution: ExecutionResult,
    report: ResearchReport,
) -> CoverageResult:
    """
    Compare planned task retrieval with final report content.

    This is a structural coverage check.

    It does not prove that findings actually answer
    the research objective or that claims are correct.
    """

    report_urls = {
        paper.url
        for paper in report.papers
    }

    finding_urls = [
        finding.source_url
        for finding in report.key_findings
    ]

    collected_urls = {
        paper["url"]
        for paper in execution.papers
    }

    # Reject inconsistent test/integration data.
    if not report_urls.issubset(collected_urls):
        raise ValueError(
            "Final report contains sources not present "
            "in the execution results."
        )

    task_coverage = []

    for task in execution.tasks:

        retrieved_urls = set(task.paper_urls)

        included_urls = (
            retrieved_urls & report_urls
        )

        linked_findings = sum(
            url in included_urls
            for url in finding_urls
        )

        notes = []

        if task.status == "failed":
            status = "search_failed"
            notes.append(
                "The OpenAlex search failed."
            )

        elif task.status == "skipped":
            status = "search_skipped"
            notes.append(
                "The planned search was not executed."
            )

        elif not retrieved_urls:
            status = "no_sources"
            notes.append(
                "No usable papers were retrieved."
            )

        elif not included_urls:
            status = "retrieved_only"
            notes.append(
                "Papers were retrieved but none were "
                "included in the final report."
            )

        elif linked_findings == 0:
            status = "no_linked_findings"
            notes.append(
                "Papers were included, but no finding "
                "cited them."
            )

        else:
            status = "evidence_linked"
            notes.append(
                "At least one finding cites a paper "
                "retrieved for this task."
            )

        task_coverage.append(
            TaskCoverage(
                title=task.title,
                query=task.query,
                execution_status=task.status,
                coverage_status=status,
                retrieved_papers=len(retrieved_urls),
                included_papers=len(included_urls),
                findings_linked=linked_findings,
                notes=notes,
            )
        )

    return CoverageResult(
        objective=execution.objective,
        tasks=task_coverage,
    )
