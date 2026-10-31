
from pydantic import ValidationError

from planner import ResearchPlan, ResearchTask


# ─────────────────────────────────────────
# TEST 1: VALID PLAN
# ─────────────────────────────────────────

valid_plan = ResearchPlan(
    objective="Compare reinforcement learning and PID control",
    tasks=[
        ResearchTask(
            title="PID Control",
            purpose="Investigate traditional PID control methods.",
            search_query="PID mobile robot control",
        ),
        ResearchTask(
            title="Reinforcement Learning",
            purpose="Investigate reinforcement learning control.",
            search_query="reinforcement learning mobile robots",
        ),
    ],
)

assert len(valid_plan.tasks) == 2

print("TEST 1 PASSED: Valid plan accepted")


# ─────────────────────────────────────────
# TEST 2: EMPTY TASK LIST
# ─────────────────────────────────────────

try:
    ResearchPlan(
        objective="Compare robot control strategies",
        tasks=[],
    )
except ValidationError:
    print("TEST 2 PASSED: Empty tasks rejected")
else:
    raise AssertionError(
        "Empty task list was incorrectly accepted."
    )


# ─────────────────────────────────────────
# TEST 3: DUPLICATE SEARCH QUERIES
# ─────────────────────────────────────────

try:
    ResearchPlan(
        objective="Compare robot control strategies",
        tasks=[
            ResearchTask(
                title="First approach",
                purpose="Investigate control performance.",
                search_query="PID robot control",
            ),
            ResearchTask(
                title="Second approach",
                purpose="Investigate implementation costs.",
                search_query="  pid ROBOT control  ",
            ),
        ],
    )
except ValidationError:
    print("TEST 3 PASSED: Duplicate queries rejected")
else:
    raise AssertionError(
        "Duplicate queries were incorrectly accepted."
    )


print("\nALL PLANNER SCHEMA TESTS PASSED")
