
from schemas import ResearchPaper, ResearchFinding, ResearchReport
from verification import verify_evidence

source_papers = [{
    "title": "Example Robotics Paper",
    "year": 2025,
    "url": "https://openalex.org/W123",
    "citations": 20,
    "abstract": (
        "The robot achieved an 82% success rate in simulation."
    )
}]

paper = ResearchPaper(
    title="Example Robotics Paper",
    year=2025,
    url="https://openalex.org/W123",
    citations=20,
    summary="Research on robot performance."
)

finding = ResearchFinding(
    claim="The robot achieved a 98% success rate in simulation.",
    evidence="The robot achieved an 82% success rate in simulation.",
    source_url="https://openalex.org/W123"
)

report = ResearchReport(
    topic="Robotic Performance",
    papers=[paper],
    key_findings=[finding],
    overall_summary="Research on robot success rates."
)

errors = verify_evidence(report, source_papers)

print("Verification errors:", errors)
print("Claim:", finding.claim)
print("Evidence:", finding.evidence)
