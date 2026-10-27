import os
import requests

from dotenv import load_dotenv
from pydantic_ai import Agent
from research import search_papers

load_dotenv()

agent = Agent(
    "google:gemini-3.5-flash-lite",
    instructions=(
        "You are Trace, a scientific research assistant. "
        "When asked to find academic research papers, "
        "use the search_openalex tool. "
        "Only mention retrieved papers that appear in "
        "the tool results. Provide their titles, years, "
        "and source links. Do not invent citations. "
        "If the search fails, explain the limitation."
    ),
)


@agent.tool_plain
def search_openalex(query: str, max_results: int = 3) -> list[dict]:
    """Search the OpenAlex academic database for research papers.

    Args:
        query: Keywords describing the research topic.
        max_results: Number of results to retrieve, from 1 to 10.
    """
    print(f"\n[TOOL CALLED] search_openalex")
    print(f"Query: {query}")
    print(f"Results requested: {max_results}")

    try:
        return search_papers(query, max_results)

    except (requests.exceptions.RequestException, ValueError) as error:
        return [{"error": str(error)}]


def main():
    question = input("\nTRACE > ").strip()

    if not question:
        print("Please enter a question.")
        return

    try:
        result = agent.run_sync(question)

        print("\n--- TRACE RESEARCH RESULTS ---\n")
        print(result.output)

    except Exception as error:
        print(f"\n[ERROR] {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
