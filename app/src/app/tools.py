from .embed import EmbeddingModel
from .vector_db import VectorDB
from .config import settings

import logging

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger(__name__)

vector_db = VectorDB(
    base_url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
)

embedding_model = EmbeddingModel(
    base_url=f"{settings.openai_base_url}/embeddings",
    api_key=settings.openai_api_key,
    model_name=settings.embedding_model,
)

def get_ekn_description(
    ekn: str,
) -> str:
    results = vector_db.filter_for_category(
        category_name="EKN",
        filter_value=ekn,
        collection_name=settings.ekn_collection_name,
    )

    if len(results) > 0:
        first = results[0]
        return str(first.payload)

    log.debug(f"Retrieved results: {results}.")
    return "Loading description failed"

def semantic_search(
    query_text: str,
    collection_name: str,
    filter_file_name: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Semantic search over one corpus collection, optionally restricted to a single source file."""
    embeddings = embedding_model.embed(query_text)
    result = vector_db.search(
        search_vector=embeddings,
        collection_name=collection_name,
        filter_file_name=filter_file_name,
        limit=limit,
    )

    log.debug(f"Retrieved results: {result}.")
    return [point.payload for point in result.points]

# Legacy entry points, still used by app.agents; app.subagents uses semantic_search directly.
def semantic_search_control_lists(
    query_text: str,
    filter_file_name: str | None = None,
) -> list[dict]:
    return semantic_search(query_text, settings.ekn_collection_name, filter_file_name)

def semantic_search_legislation(
    query_text: str,
    filter_file_name: str | None = None,
) -> list[dict]:
    return semantic_search(query_text, settings.legislation_collection_name, filter_file_name)
