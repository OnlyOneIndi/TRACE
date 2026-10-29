
from schemas import ResearchPaper, ResearchReport
from storage import save_report

print("TRACE STORAGE TEST STARTED")

paper = ResearchPaper(
    title="Sample Robotics Paper",
    year=2025,
    url="https://example.com/paper",
    citations=10,
    summary="A sample summary."
)

report = ResearchReport(
    topic="Robot Manipulation",
    papers=[paper],
    key_findings=["Sample finding"],
    overall_summary="A test report."
)

path = save_report(report)

print("Saved successfully!")
print("File:", path)
print("Exists:", path.exists())

loaded_report = ResearchReport.model_validate_json(
    path.read_text(encoding="utf-8")
)

print("Loaded topic:", loaded_report.topic)
print("Loaded papers:", len(loaded_report.papers))
