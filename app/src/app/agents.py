from __future__ import annotations

import csv
import logging
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings
from .models import AdviseClassificationResponse, AdviseTransactionResponse
from .tools import (
    get_ekn_description,
    semantic_search_control_lists,
    semantic_search_legislation,
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
    query_result = semantic_search_control_lists(query_text) 
    log.debug(f"QUERY: {query_text}; RETRIEVED: {query_result}")
    return query_result

country_codes = ""
with open(f'{Path(config.data_dir)}/country_codes_ISO-3166.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        country_codes += ",".join(row) + "\n"

transaction_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    output_type=AdviseTransactionResponse,
    instructions=f"""
You assess the given transaction using all the information you received.

To define the verdict follow these explanations:

    NO_LICENCE_REQUIRED: nothing subjects this shipment to a licence
    LICENCE_REQUIRED: a licence is needed; name the regime and the authority
    PROHIBITED: an embargo or absolute prohibition applies
    REFER_TO_AUTHORITY: the law does not settle it, or the facts are insufficient. Note that if this option is chosen, the top-level refer_to_authority field should also be set to true.

If a license is required the authority is always "SECO", else leave this unspecified.

The answer should reference on the citations used.

For the citations return a list of document names and links to articles, e.g., ["GKV Art. 3"]

The following list contains country codes used in the routing. Check if any of the countries are on an embargo list:

{country_codes}
    """,
)

@transaction_agent.tool
def search_legislation(
    query_text: str
) -> list[dict]:
    """
    Searches the legal database and returns matching passages.
    """
    query_result = semantic_search_legislation(query_text) 
    log.debug(f"QUERY: {query_text}; RETRIEVED: {query_result}")
    return query_result

with open(f'{Path(config.corpus_dir)}/track2_data/parties/internal_flagged.json') as f:
    internal_flagged_entities = json.load(f)
diversion_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    output_type=bool,
    instructions=f"""
    Your job is to check whether the given company is on the flagged list below (return true) or not (return false).

    {internal_flagged_entities}
"""
)

with open(f'{Path(config.corpus_dir)}/track2_data/parties/public_sanctions.json') as f:
    public_sanctioned_entities = json.load(f)
public_sanction_agent = Agent(
    build_model(),
    deps_type=AgentDependencies,
    output_type=bool,
    instructions=f"""
    Your job is to check whether the given company is on the flagged list below (return true) or not (return false).

    {public_sanctioned_entities}
"""
)
