from pydantic_ai import RunContext
from app.src.app.agents import AgentDependencies

def get_ekn_description(
    ctx: RunContext[AgentDependencies],
    ekn: str,
    collection_name: str,
) -> str:
    results = ctx.deps.vector_db.filter_for_category(
        category_name="EKN",
        filter_value=ekn,
        collection_name=collection_name,
    )

    if len(results) > 0:
        first = results[0]
        return str(first.payload)

    return "Loading description failed"

def query_vector_db(
    ctx: RunContext[AgentDependencies],
    query_text: str,
    collection_name: str,
) -> list[dict]:
    embeddings = ctx.deps.embedding_model.embed(query_text)
    result = ctx.deps.vector_db.search(
        search_vector=embeddings,
        collection_name=collection_name,
        limit=20,
    )

    return [point.payload for point in result.points]
