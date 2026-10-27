import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.openalex.org/works"


def search_papers(query: str, max_results: int = 5) -> list[dict]:
    """Search OpenAlex for academic publications."""

    if not query.strip():
        raise ValueError("The search query cannot be empty.")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10.")

    parameters = {
        "search": query,
        "per_page": max_results
    }

    api_key = os.getenv("OPENALEX_API_KEY")

    if api_key:
        parameters["api_key"] = api_key

    response = requests.get(
        API_URL,
        params=parameters,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    papers = []

    for item in data["results"]:
        paper = {
            "title": item["display_name"],
            "year": item["publication_year"],
            "url": item["id"],
            "citations": item["cited_by_count"]
        }

        papers.append(paper)

    return papers


if __name__ == "__main__":
    results = search_papers(
        "intelligent machines",
        max_results=3
    )

    for paper in results:
        print(paper)
