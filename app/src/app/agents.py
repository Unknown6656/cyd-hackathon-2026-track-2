from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings
from .tools import calculate_average, calculate_percentage_change, calculate_result

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


# ---------------------------------------------------------------------------
# Agent 2
# ---------------------------------------------------------------------------

analysis_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    instructions="""
    You are a data analysis assistant.

    Your job is to analyze collections of numerical data.

    Use the tools available to you for calculations rather than estimating
    or manually calculating results.

    Explain what the calculated result means in the context of the user's
    question. Do not claim to have performed analysis that you did not
    perform.
    """,
)


@analysis_agent.tool
def calculate_average_tool(
    ctx: RunContext[AgentDependencies],
    values: list[float],
) -> float:
    """
    Calculate the average of a list of values.
    """
    return calculate_average(values)

