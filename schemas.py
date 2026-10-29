
from pydantic import BaseModel, Field

class ResearchFinding(BaseModel):
    claim: str
    evidence: str
    source_url: str
class ResearchPaper(BaseModel):
    title: str
    year: int | None = None
    url: str
    citations: int
    summary: str


class ResearchReport(BaseModel):
    topic: str
    papers: list[ResearchPaper]
    key_findings: list[ResearchFinding]
    overall_summary: str
