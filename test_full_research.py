from research_coverage import assess_research_coverage
from planner import create_research_plan

from executor import execute_research_plan

from synthesizer import (
    synthesize_research,
    SynthesisError,
)


def main():
    question = input(
        "\nTRACE RESEARCH OBJECTIVE > "
    ).strip()

    if not question:
        print("Please enter a research objective.")
        return

    try:
        # 1. PLAN
        print("\n[1/3] CREATING RESEARCH PLAN")

        plan = create_research_plan(question)

        print("\n--- PLAN ---")
        print(plan.model_dump_json(indent=2))

        # 2. EXECUTE
        print("\n[2/3] RETRIEVING EVIDENCE")

        execution = execute_research_plan(
            plan=plan,
            papers_per_task=2,
            max_total_papers=6,
            from_year=2023,
        )

        for task in execution.tasks:
            print(
                f"{task.title}: {task.status} "
                f"({len(task.paper_urls)} papers)"
            )

            if task.error:
                print("Error:", task.error)

        print(
            "\nUnique papers collected:",
            len(execution.papers),
        )

        if not execution.papers:
            print(
                "Research stopped: no usable "
                "sources were retrieved."
            )
            return

        # 3. SYNTHESIZE
        print("\n[3/3] SYNTHESIZING RESEARCH")

        report = synthesize_research(
            execution
        )
        
        # 4. ASSESS STRUCTURAL COVERAGE
        print("\n[4/4] ASSESSING RESEARCH COVERAGE")

        coverage = assess_research_coverage(
            execution=execution,
            report=report,
        )

        for task in coverage.tasks:

            print(f"\nTask: {task.title}")
            print(f"Coverage: {task.coverage_status}")
            print(f"Retrieved: {task.retrieved_papers}")
            print(f"Included: {task.included_papers}")
            print(f"Linked findings: {task.findings_linked}")

            for note in task.notes:
                print("Note:", note)

        print(
            "\nTASKS WITH LINKED FINDINGS:",
            coverage.evidence_linked_tasks,
            "/",
            coverage.total_tasks,
        )

        print("\n--- VERIFIED RESEARCH REPORT ---")
        print(report.model_dump_json(indent=2))

        print("\nSYNTHESIS CHECKS PASSED")

        # Deliberately do not save here.
        # We'll integrate audit-backed storage later.

    except SynthesisError as error:
        print("\n[SYNTHESIS VERIFICATION FAILED]")
        print(error)

    except Exception as error:
        print(
            f"\n[RESEARCH ERROR] "
            f"{type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    main()
