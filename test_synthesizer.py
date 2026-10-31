
from schemas import (
    ResearchPaper,
    ResearchFinding,
    ResearchReport,
)

from synthesizer import (
    validate_synthesis,
    SynthesisError,
)


source_papers = [
    {
        "title": "Robot Control Study",
        "year": 2024,
        "url": "https://openalex.org/W123",
        "citations": 12,
        "abstract": (
            "The robot controller achieved 82% accuracy "
            "during experimental testing."
        ),
    }
]


def make_report(evidence):
    return ResearchReport(
        topic="Robot Control",
        papers=[
            ResearchPaper(
                title="Robot Control Study",
                year=2025,  # Intentionally incorrect
                url="https://openalex.org/W123",
                citations=99,  # Intentionally incorrect
                summary="A study of robot control.",
            )
        ],
        key_findings=[
            ResearchFinding(
                claim=(
                    "The controller achieved "
                    "82% accuracy."
                ),
                evidence=evidence,
                source_url="https://openalex.org/W123",
            )
        ],
        overall_summary=(
            "The study reports an experimental result."
        ),
    )


# TEST 1: VALID EVIDENCE
report = make_report(
    "The robot controller achieved 82% accuracy "
    "during experimental testing."
)

validated = validate_synthesis(
    report,
    source_papers,
)

assert validated.papers[0].year == 2024
assert validated.papers[0].citations == 12

print("TEST 1 PASSED: Metadata restored")


# TEST 2: FABRICATED EVIDENCE
try:
    validate_synthesis(
        make_report(
            "The robot controller achieved "
            "99% accuracy."
        ),
        source_papers,
    )

except SynthesisError:
    print("TEST 2 PASSED: Fabricated evidence rejected")

else:
    raise AssertionError(
        "Fabricated evidence was accepted."
    )


print("\nALL SYNTHESIS TESTS PASSED")
