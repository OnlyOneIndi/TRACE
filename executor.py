
from dataclasses import dataclass, field
from datetime import datetime

import requests

from planner import ResearchPlan
from research import search_papers


# ─────────────────────────────────────────
# EXECUTION RESULTS
# ─────────────────────────────────────────

@dataclass
class TaskResult:
    title: str
    query: str
    status: str
    paper_urls: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class ExecutionResult:
    objective: str
    tasks: list[TaskResult]
    papers: list[dict]

    @property
    def successful_tasks(self) -> int:
        return sum(
            task.status == "completed"
            for task in self.tasks
        )


# ─────────────────────────────────────────
# PLAN EXECUTOR
# ─────────────────────────────────────────

def execute_research_plan(
    plan: ResearchPlan,
    papers_per_task: int = 3,
    max_total_papers: int = 10,
    from_year: int | None = None,
) -> ExecutionResult:
    """
    Execute a research plan using OpenAlex.

    One search is performed for each task, subject
    to the overall paper limit.

    This function retrieves evidence. It does not
    ask Gemini to generate research conclusions.
    """

    if not 1 <= papers_per_task <= 10:
        raise ValueError(
            "papers_per_task must be between 1 and 10."
        )

    if not 1 <= max_total_papers <= 50:
        raise ValueError(
            "max_total_papers must be between 1 and 50."
        )

    if from_year is not None:
        if (
            not isinstance(from_year, int)
            or not 1900 <= from_year <= datetime.now().year
        ):
            raise ValueError(
                "Invalid earliest publication year."
            )

    collected_papers = {}
    task_results = []

    for task in plan.tasks:

        remaining = (
            max_total_papers - len(collected_papers)
        )

        if remaining <= 0:
            task_results.append(
                TaskResult(
                    title=task.title,
                    query=task.search_query,
                    status="skipped",
                    error="Overall paper limit reached.",
                )
            )
            continue

        search_limit = min(
            papers_per_task,
            remaining,
        )

        try:
            papers = search_papers(
                query=task.search_query,
                max_results=search_limit,
                from_year=from_year,
            )

            if not papers:
                task_results.append(
                    TaskResult(
                        title=task.title,
                        query=task.search_query,
                        status="empty",
                    )
                )
                continue

            task_urls = []

            for paper in papers:
                url = paper.get("url")

                if not url:
                    continue

                # Check the returned data independently.
                year = paper.get("year")

                if from_year is not None:
                    if year is None or year < from_year:
                        continue

                task_urls.append(url)

                if url not in collected_papers:
                    if len(collected_papers) >= max_total_papers:
                        break

                    collected_papers[url] = paper

            task_results.append(
                TaskResult(
                    title=task.title,
                    query=task.search_query,
                    status=(
                        "completed"
                        if task_urls
                        else "empty"
                    ),
                    paper_urls=list(dict.fromkeys(task_urls)),
                )
            )

        except (
            requests.exceptions.RequestException,
            ValueError,
        ) as error:

            task_results.append(
                TaskResult(
                    title=task.title,
                    query=task.search_query,
                    status="failed",
                    error=str(error),
                )
            )

    return ExecutionResult(
        objective=plan.objective,
        tasks=task_results,
        papers=list(collected_papers.values()),
    )
