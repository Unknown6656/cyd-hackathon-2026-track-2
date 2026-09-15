from __future__ import annotations

import logging
import json
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings
from .data import internal_flagged_entities_str
from .models import AdviseClassificationResponse
from .tools import (
    get_ekn_description,
    query_vector_db,
)

config = Settings()

logging.basicConfig(
    level=config.log_level,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger(__name__)


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



classifier_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    output_type=AdviseClassificationResponse,
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
    query_result = get_ekn_description(ekn) 
    log.debug(f"EKN: {ekn}; RETRIEVED: {query_result}")
    return query_result

@classifier_agent.tool
def search_ordinances(
    ctx: RunContext[AgentDependencies],
    query_text: str,
) -> list[dict]:
    """
    Searches the legal database of ordinances and returns matching passages.
    """
    query_result = query_vector_db(query_text) 
    log.debug(f"QUERY: {query_text}; RETRIEVED: {query_result}")
    return query_result


internal_flagged_entities = json.loads(internal_flagged_entities_str)
diversion_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    output_type=bool,
    instructions=f"""
    Your job is to check whether the given company is on the flagged list below (return true) or not (return false).

    {internal_flagged_entities}
"""
)