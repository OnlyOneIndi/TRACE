from pathlib import Path
from planner import create_research_plan
from executor import execute_research_plan
from synthesizer import synthesize_research, SynthesisError
from storage import save_report
from audit import save_verification_audit


class ResearchVerificationError(Exception):
    """Raised when the planned research workflow is rejected."""


def run_research(
    question: str,
    max_papers: int = 6,
    from_year: int | None = None,
) -> tuple:
    """
    Run the planned research pipeline.

    PLAN -> EXECUTE -> SYNTHESIZE -> VERIFY
    -> SAVE -> AUDIT

    Returns:
        (ResearchReport, saved Path)
    """

    question = question.strip()

    if not question:
        raise ValueError(
            "Research question cannot be empty."
        )

    if type(max_papers) is not int or not 1 <= max_papers <= 10:
        raise ValueError(
            "Maximum papers must be an integer between 1 and 10."
        )


    # 1. GENERATE RESEARCH PLAN
    plan = create_research_plan(question)

    # Our first integrated version aims to retrieve
    # at least one source for each planned task.
    if max_papers < len(plan.tasks):
        raise ResearchVerificationError(
            f"The planner created {len(plan.tasks)} tasks, "
            f"but the paper limit is only {max_papers}. "
            "Increase the maximum papers setting to "
            f"at least {len(plan.tasks)}."
        )

    
    # 2. EXECUTE THE PLAN
    execution = execute_research_plan(
        plan=plan,
        papers_per_task=2,
        max_total_papers=max_papers,
        from_year=from_year,
    )

    failed_tasks = [
        task
        for task in execution.tasks
        if task.status == "failed"
    ]

    if failed_tasks:
        details = "\n".join(
            f"- {task.title}: {task.error}"
            for task in failed_tasks
        )

        raise ResearchVerificationError(
            "One or more planned research searches failed:\n"
            + details
        )

    if not execution.papers:
        raise ResearchVerificationError(
            "The research plan produced no usable papers."
        )

    # Prevent silently accepting an investigation
    # in which planned tasks were skipped.
    skipped_tasks = [
        task.title
        for task in execution.tasks
        if task.status == "skipped"
    ]

    if skipped_tasks:
        raise ResearchVerificationError(
            "The paper limit was reached before all "
            "planned tasks could run. Increase the "
            "maximum papers setting and retry.\n"
            + "\n".join(skipped_tasks)
        )

    # ─────────────────────────────────────
    # 3. SYNTHESIZE AND VERIFY
    # ─────────────────────────────────────

    try:
        report = synthesize_research(execution)

    except SynthesisError as error:
        raise ResearchVerificationError(
            f"Research synthesis failed verification:\n{error}"
        ) from error

    # ─────────────────────────────────────
    # 4. ENFORCE FINAL CONSTRAINTS
    # ─────────────────────────────────────

    if len(report.papers) > max_papers:
        raise ResearchVerificationError(
            "The synthesized report exceeds "
            "the selected paper limit."
        )

    if from_year is not None:
        for paper in report.papers:
            if paper.year is None or paper.year < from_year:
                raise ResearchVerificationError(
                    "Report contains a paper outside "
                    "the selected publication-year range: "
                    + paper.title
                )

    # synthesize_research() has already checked:
    # - Paper metadata against retrieved records
    # - Evidence quotations against abstracts
    # - Selected numerical consistency
    # - Finding-to-paper source relationships
    #
    # Record these successful checks in the audit.

    checks = {
        "research_constraints": True,
        "source_metadata": True,
        "evidence_quotations": True,
        "numerical_consistency": True,
    }

    # ─────────────────────────────────────
    # 5. SAVE REPORT AND AUDIT
    # ─────────────────────────────────────

    saved_path = save_report(report)

    try:
        save_verification_audit(
            report_path=saved_path,
            retrieved_papers=execution.papers,
            max_papers=max_papers,
            from_year=from_year,
            checks=checks,
        )

    except Exception as error:
        # Avoid leaving a report that appears
        # accepted but has no completed audit.
        saved_path.with_suffix(
            ".audit.json"
        ).unlink(missing_ok=True)

        saved_path.unlink(missing_ok=True)

        raise RuntimeError(
            "The research report passed verification, "
            "but its audit could not be saved."
        ) from error

    return report, saved_path
