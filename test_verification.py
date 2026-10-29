from schemas import ResearchPaper, ResearchReport
from verification import verify_report


# Simulated data retrieved from OpenAlex
source_papers = [
    {
        "title": "Example Robotics Paper",
        "year": 2023,
        "url": "https://openalex.org/W123",
        "citations": 45
    }
]


# A paper with correct metadata
paper = ResearchPaper(
    title="Example Robotics Paper",
    year=2023,
    url="https://openalex.org/W123",
    citations=45,
    summary="An example research summary."
)


def create_report(papers):
    return ResearchReport(
        topic="Robotic Manipulation",
        papers=papers,
        key_findings=["Example finding"],
        overall_summary="An example research report."
    )


def run_test(test_name, papers, should_pass):
    print(f"\n--- {test_name} ---")

    report = create_report(papers)
    errors = verify_report(report, source_papers)

    if errors:
        print("VERIFICATION FAILED")
        for error in errors:
            print("-", error)
    else:
        print("VERIFICATION PASSED")

    actual_pass = not errors

    assert actual_pass == should_pass, (
        f"Unexpected verification result in {test_name}"
    )

    print("TEST PASSED")


# Test 1: Correct paper metadata
run_test(
    "Correct Metadata",
    papers=[paper],
    should_pass=True
)


# Test 2: Empty list of papers
run_test(
    "Empty Papers",
    papers=[],
    should_pass=False
)


# Test 3: Duplicate paper URLs
run_test(
    "Duplicate Papers",
    papers=[paper, paper],
    should_pass=False
)

print("\nALL THREE TESTS PASSED!")
