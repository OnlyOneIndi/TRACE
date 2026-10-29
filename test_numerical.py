
from schemas import ResearchPaper, ResearchFinding, ResearchReport
from verification import check_numerical_consistency


paper = ResearchPaper(
    title="Example Robotics Paper",
    year=2025,
    url="https://openalex.org/W123",
    citations=20,
    summary="An example robotics study."
)


def make_report(claim, evidence):
    finding = ResearchFinding(
        claim=claim,
        evidence=evidence,
        source_url="https://openalex.org/W123"
    )

    return ResearchReport(
        topic="Robotic Performance",
        papers=[paper],
        key_findings=[finding],
        overall_summary="An example research report."
    )


def run_test(name, claim, evidence, expect_warning):
    report = make_report(claim, evidence)

    warnings = check_numerical_consistency(report)

    print(f"\n--- {name} ---")
    print("Warnings:", warnings)

    assert bool(warnings) == expect_warning

    print("TEST PASSED")


# Test 1: Matching percentages
run_test(
    name="Matching Percentages",
    claim="The robot achieved 82% success.",
    evidence="The robot achieved an 82% success rate.",
    expect_warning=False
)


# Test 2: Conflicting percentages
run_test(
    name="Conflicting Percentages",
    claim="The robot achieved 98% success.",
    evidence="The robot achieved an 82% success rate.",
    expect_warning=True
)


# Test 3: Decimal percentages
run_test(
    name="Decimal Percentages",
    claim="The system achieved 92.5% accuracy.",
    evidence="Accuracy reached 92.5% during testing.",
    expect_warning=False
)


# Test 4: Extra percentage in claim
run_test(
    name="Unsupported Additional Percentage",
    claim="Accuracy was 90% and recall was 85%.",
    evidence="The model achieved 90% accuracy.",
    expect_warning=True
)


print("\nALL FOUR NUMERICAL TESTS PASSED!")
