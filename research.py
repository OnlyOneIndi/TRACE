
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.openalex.org/works"


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """Convert an OpenAlex inverted index into readable text."""

    if not inverted_index:
        return None

    word_positions = []

    for word, positions in inverted_index.items():
        for position in positions:
            word_positions.append((position, word))

    word_positions.sort()

    abstract = " ".join(
        word for position, word in word_positions
    )

    return abstract


def search_papers(
    query: str,
    max_results: int = 3,
    from_year: int | None = None
) -> list[dict]:
    """Search OpenAlex for academic publications."""

    if not query.strip():
        raise ValueError("The search query cannot be empty.")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10.")

    parameters = {
        "search": query,
        "per_page": max_results
    }

    if from_year is not None:
        if not 1900 <= from_year <= 2100:
            raise ValueError("Invalid publication year.")

        parameters["filter"] = (
            f"from_publication_date:{from_year}-01-01"
        )

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
        abstract = reconstruct_abstract(
            item.get("abstract_inverted_index")
        )

        paper = {
            "title": item["display_name"],
            "year": item["publication_year"],
            "url": item["id"],
            "citations": item["cited_by_count"],
            "abstract": abstract
        }

        papers.append(paper)

    return papers


if __name__ == "__main__":
    results = search_papers(
        "robot manipulation",
        max_results=3,
        from_year=2023
    )

    for paper in results:
        print("\nTITLE:", paper["title"])
        print("ABSTRACT:", paper["abstract"])
        print("-" * 50)
