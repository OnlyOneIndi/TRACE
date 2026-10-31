
from executor import ExecutionResult, TaskResult
from schemas import (
    ResearchReport,
    ResearchPaper,
    ResearchFinding,
)
from research_coverage import assess_research_coverage


# ─────────────────────────────────────────
# SIMULATED EXECUTOR OUTPUT
# ─────────────────────────────────────────

execution = ExecutionResult(
    objective="Compare robot control approaches",
    tasks=[
        TaskResult(
            title="PID Control",
            query="PID robot control",
            status="completed",
            paper_urls=[
                "https://openalex.org/W101"
            ],
        ),
        TaskResult(
            title="Reinforcement Learning",
            query="reinforcement learning robots",
            status="completed",
            paper_urls=[
                "https://openalex.org/W102"
            ],
        ),
        TaskResult(
            title="Computational Cost",
            query="robot control computational cost",
            status="empty",
            paper_urls=[],
        ),
    ],
    papers=[
        {
            "title": "PID Research",
            "year": 2024,
            "url": "https://openalex.org/W101",
            "citations": 10,
            "abstract": "PID control study.",
        },
        {
            "title": "RL Research",
            "year": 2025,
            "url": "https://openalex.org/W102",
            "citations": 8,
            "abstract": "Reinforcement learning study.",
        },
    ],
)


# ─────────────────────────────────────────
# SIMULATED FINAL REPORT
# ─────────────────────────────────────────

report = ResearchReport(
    topic="Robot Control Comparison",
    papers=[
        ResearchPaper(
            title="PID Research",
            year=2024,
            url="https://openalex.org/W101",
            citations=10,
            summary="PID control study.",
        ),
        ResearchPaper(
            title="RL Research",
            year=2025,
            url="https://openalex.org/W102",
            citations=8,
            summary="Reinforcement learning study.",
        ),
    ],
    key_findings=[
        ResearchFinding(
            claim="PID control was investigated.",
            evidence="PID control study.",
            source_url="https://openalex.org/W101",
        )
    ],
    overall_summary="A comparison of robot control.",
)


# ─────────────────────────────────────────
# TEST COVERAGE
# ─────────────────────────────────────────

coverage = assess_research_coverage(
    execution,
    report,
)

assert coverage.total_tasks == 3
assert coverage.evidence_linked_tasks == 1

statuses = {
    task.title: task.coverage_status
    for task in coverage.tasks
}

assert statuses["PID Control"] == "evidence_linked"
assert statuses["Reinforcement Learning"] == "no_linked_findings"
assert statuses["Computational Cost"] == "no_sources"

assert len(coverage.incomplete_tasks) == 2

print("TEST 1 PASSED: Coverage statuses are correct")
print("TEST 2 PASSED: Missing evidence links detected")
print("TEST 3 PASSED: Empty research task detected")

print("\nALL COVERAGE TESTS PASSED")
