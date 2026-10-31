
from planner import create_research_plan
from executor import execute_research_plan


def main():
    question = input(
        "\nTRACE RESEARCH OBJECTIVE > "
    ).strip()

    if not question:
        print("Please enter a research objective.")
        return

    print("\n[1/2] CREATING RESEARCH PLAN")

    plan = create_research_plan(question)

    print("\n--- GENERATED PLAN ---")
    print(plan.model_dump_json(indent=2))

    print("\n[2/2] EXECUTING OPENALEX SEARCHES")

    result = execute_research_plan(
        plan=plan,
        papers_per_task=2,
        max_total_papers=8,
        from_year=2023,
    )

    print("\n--- EXECUTION RESULTS ---")

    for task in result.tasks:
        print(f"\nTask: {task.title}")
        print(f"Query: {task.query}")
        print(f"Status: {task.status}")
        print(f"Papers linked: {len(task.paper_urls)}")

        if task.error:
            print(f"Error: {task.error}")

    print("\n--- COLLECTED PAPERS ---")

    for index, paper in enumerate(
        result.papers,
        start=1,
    ):
        print(f"\n{index}. {paper['title']}")
        print(f"Year: {paper['year']}")
        print(f"URL: {paper['url']}")

    print(
        f"\nTOTAL UNIQUE PAPERS: {len(result.papers)}"
    )

    if not result.papers:
        print(
            "No research papers were collected. "
            "Inspect task statuses and search queries."
        )


if __name__ == "__main__":
    main()
