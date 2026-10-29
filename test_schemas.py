
from schemas import ResearchPaper, ResearchReport

paper = ResearchPaper(
    title="Example Robotics Study",
    year=2025,
    url="https://example.com/paper",
    citations=42,
    summary="A study investigating robotic manipulation."
)

report = ResearchReport(
    topic="Robotic Manipulation",
    papers=[paper],
    key_findings=[
        "Robotic systems can learn manipulation strategies."
    ],
    overall_summary="An overview of robotics research."
)

print(report.model_dump_json(indent=2))
