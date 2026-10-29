
from schemas import (
    ResearchPaper,
    ResearchFinding,
    ResearchReport,
)

from verification import verify_evidence


# Simulated OpenAlex research record
source_papers = [
    {
        "title": "Example Robotics Paper",
        "year": 2023,
        "url": "https://openalex.org/W123",
        "citations": 45,
        "abstract": (
            "The robotic system achieved an 82% "
            "task-success rate in simulation."
        ),
    }
]


# Create a paper with valid metadata
paper = ResearchPaper(
    title="Example Robotics Paper",
    year=2023,
    url="https://openalex.org/W123",
    citations=45,
    summary="A study of robotic task performance."
)


def create_report(evidence: str) -> ResearchReport:
    """Create a sample report with the given evidence."""

    finding = ResearchFinding(
        claim="The robot achieved 82% success in simulation.",
        evidence=evidence,
        source_url="https://openalex.org/W123"
    )

    return ResearchReport(
        topic="Robotic Systems",
        papers=[paper],
        key_findings=[finding],
        overall_summary="A sample research report."
    )


def run_test(
    test_name: str,
    evidence: str,
    should_pass: bool
):
    """Test whether evidence verification behaves correctly."""

    print(f"\n--- {test_name} ---")

    report = create_report(evidence)

    errors = verify_evidence(
        report=report,
        source_papers=source_papers
    )

    if errors:
        print("EVIDENCE VERIFICATION FAILED")

        for error in errors:
            print("-", error)

    else:
        print("EVIDENCE VERIFICATION PASSED")

    actual_pass = not errors

    assert actual_pass == should_pass, (
        f"Unexpected result in {test_name}"
    )

    print("TEST PASSED")


# TEST 1: Evidence actually appears in the abstract
run_test(
    test_name="Valid Evidence",
    evidence="82% task-success rate in simulation",
    should_pass=True
)


# TEST 2: Fabricated evidence
run_test(
    test_name="Fabricated Evidence",
    evidence="98% success rate in real-world tests",
    should_pass=False
)


# TEST 3: Empty evidence
run_test(
    test_name="Empty Evidence",
    evidence="",
    should_pass=False
)


print("\nALL THREE EVIDENCE TESTS PASSED!")
