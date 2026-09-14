from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings
from .tools import (
    calculate_percentage_change,
    calculate_result,
    get_ekn_description,
)

config = Settings()


def build_model() -> OpenAIChatModel:
    """Build an OpenAI-compatible model from the application settings."""
    provider = OpenAIProvider(
        base_url=config.openai_base_url,
        api_key=config.openai_api_key,
    )
    return OpenAIChatModel(config.model, provider=provider)


@dataclass
class AgentDependencies:
    """
    Runtime dependencies available to tools.

    Keep things like database clients, API clients, configuration, etc.
    here rather than putting them in global variables.
    """

    # db: Database
    # settings: Settings
    # calculator: Calculator




# ---------------------------------------------------------------------------
# Agent 1
# ---------------------------------------------------------------------------

classifier_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    instructions="""
You answer the user's question using the supplied semantic-search results.

The search results may contain references to additional entries (via a EKN number: "Exportkontrollnummer").

When you encounter a reference that is relevant to answering the question,
use the `get_ekn_description` tool to retrieve its text.

You may call the tool multiple times and should retrieve all references
that are necessary to produce a reliable answer.

Do not invent the contents of references.

Once you have enough information, provide the final answer.
    """,
)

@classifier_agent.tool
def get_ekn_description_tool(
    ctx: RunContext[AgentDependencies],
    ekn: str,
) -> str:
    """
    Fetches the text description of a good given its EKN identifier.
    """
    return get_ekn_description(ekn)

# ---------------------------------------------------------------------------
# Agent 1
# ---------------------------------------------------------------------------

calculation_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    instructions="""
    You are a calculation assistant.

    Your job is to answer questions that require numerical calculations.

    Use your available calculation tools whenever an exact calculation
    is required. Do not perform calculations yourself when a tool exists
    for the operation.

    Explain the result clearly and include the relevant units or context
    when they are provided by the user.
    """,
)


@calculation_agent.tool
def calculate_result_tool(
    ctx: RunContext[AgentDependencies],
    value: float,
    multiplier: float,
) -> float:
    """
    Calculate a value using the application's calculation function.
    """
    return calculate_result(value, multiplier)


@calculation_agent.tool
def calculate_percentage_change_tool(
    ctx: RunContext[AgentDependencies],
    old_value: float,
    new_value: float,
) -> float:
    """
    Calculate percentage change using the application's calculation function.
    """
    return calculate_percentage_change(old_value, new_value)