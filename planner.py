
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator
from pydantic_ai import Agent



# CONFIGURATION
load_dotenv()

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "google:gemini-3.5-flash-lite"
)



# RESEARCH PLAN SCHEMAS
class ResearchTask(BaseModel):
    """A specific task within an investigation."""

    title: str = Field(min_length=3)
    purpose: str = Field(min_length=10)
    search_query: str = Field(min_length=3)


class ResearchPlan(BaseModel):
    """A structured plan for investigating a topic."""

    objective: str = Field(min_length=5)

    tasks: list[ResearchTask] = Field(
        min_length=2,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_tasks(self):
        """Reject duplicated search queries."""

        queries = [
            " ".join(task.search_query.casefold().split())
            for task in self.tasks
        ]

        if len(queries) != len(set(queries)):
            raise ValueError(
                "Research tasks must have distinct search queries."
            )

        return self


# RESEARCH PLANNER
planner_agent = Agent(
    MODEL_NAME,
    output_type=ResearchPlan,
    instructions=(
        "You are Trace's research planning specialist. "

        "Your responsibility is to transform a research "
        "objective into a structured investigation plan. "

        "Produce between 2 and 4 meaningful research tasks. "

        "Each task must have a concise title, a clear purpose, "
        "and a focused academic search query. "

        "The tasks should investigate different but relevant "
        "aspects of the original research objective. "

        "For comparative questions, investigate the relevant "
        "approaches and the evidence needed to compare them. "

        "For explanatory questions, identify the important "
        "concepts, methods, applications or limitations. "

        "Use short, specific search queries suitable for "
        "the OpenAlex academic search engine. "

        "Do not repeat the same search query across tasks. "

        "Do not claim that research has already been performed. "

        "Do not invent research papers, findings or conclusions. "

        "You are planning research, not executing it."
    ),
)


def create_research_plan(question: str) -> ResearchPlan:
    """
    Turn a research question into a structured plan.

    This function does not search OpenAlex.
    """

    question = question.strip()

    if not question:
        raise ValueError(
            "Research question cannot be empty."
        )

    result = planner_agent.run_sync(
        "Create an investigation plan for this objective:\n\n"
        + question
    )

    return result.output


# TERMINAL TEST
if __name__ == "__main__":

    question = input(
        "\nTRACE PLANNER > "
    ).strip()

    try:
        plan = create_research_plan(question)

        print("\n--- RESEARCH PLAN ---\n")
        print(plan.model_dump_json(indent=2))

    except Exception as error:
        print(
            f"\n[PLANNER ERROR] "
            f"{type(error).__name__}: {error}"
        )
