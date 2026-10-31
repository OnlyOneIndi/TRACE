
from unittest.mock import patch

from planner import ResearchPlan, ResearchTask
from executor import execute_research_plan


plan = ResearchPlan(
    objective="Compare robot control approaches",
    tasks=[
        ResearchTask(
            title="PID Control",
            purpose="Investigate conventional robot control.",
            search_query="PID robot control",
        ),
        ResearchTask(
            title="Reinforcement Learning",
            purpose="Investigate learning-based robot control.",
            search_query="reinforcement learning robots",
        ),
    ],
)

fake_results = [
    [
        {
            "title": "PID Research",
            "year": 2024,
            "url": "https://openalex.org/W101",
            "citations": 12,
            "abstract": "Example abstract.",
        },
    ],
    [
        {
            "title": "RL Research",
            "year": 2025,
            "url": "https://openalex.org/W102",
            "citations": 8,
            "abstract": "Another example abstract.",
        },
        {
            "title": "PID Research",
            "year": 2024,
            "url": "https://openalex.org/W101",
            "citations": 12,
            "abstract": "Example abstract.",
        },
    ],
]

with patch(
    "executor.search_papers",
    side_effect=fake_results,
) as mocked_search:

    result = execute_research_plan(
        plan,
        papers_per_task=3,
        max_total_papers=5,
        from_year=2023,
    )

    assert mocked_search.call_count == 2
    assert len(result.tasks) == 2
    assert result.successful_tasks == 2

    # Duplicate W101 must appear only once.
    assert len(result.papers) == 2

    assert {
        paper["url"] for paper in result.papers
    } == {
        "https://openalex.org/W101",
        "https://openalex.org/W102",
    }

    assert all(
        paper["year"] >= 2023
        for paper in result.papers
    )

print("ALL EXECUTOR TESTS PASSED")
