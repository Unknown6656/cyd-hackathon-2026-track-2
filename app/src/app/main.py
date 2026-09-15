"""Track 2 export control advisor — minimal skeleton. Implement your advisor here.

See README.md for the full contract (request blocks, response shape, citations).
"""

from pathlib import Path
import textwrap
import json
import os

from fastapi import FastAPI

from .ingest import run_embed, run_parse

from .config import settings
from .models import *
from .backend import get_classification, semantic_search



app = FastAPI(title="Track 2 export control advisor")



@app.post("/advise")
async def advise(req: AdviseRequest) -> AdviseResponse:
    refer_to_authority: bool = False
    query_response: AdviseQueryResponse | None = None
    classification_response: AdviseClassificationResponse | None = None
    transaction_response: AdviseTransactionResponse | None = None

    if req.query is not None:
        query_response = AdviseQueryResponse(
            answer="TODO: not implemented",
            citations=[]
        )

    if req.item is not None:
        classification_context = textwrap.dedent(f'''
        # Item Description
        {req.item.description}
        
        ## (optional) Item Specification
        ```json
        {json.dumps(req.item.specifications, indent=2)}
        ```
        ''')
        classification_response = await get_classification(classification_context)

    if req.transaction is not None:
        transaction_response = AdviseTransactionResponse(
            verdict=AdviseTransactionVerdict.REFER_TO_AUTHORITY,
            authority=None,
            answer="TODO: not implemented",
            citations=[],
        )
        refer_to_authority = transaction_response.verdict == AdviseTransactionVerdict.REFER_TO_AUTHORITY

    return AdviseResponse(
        refer_to_authority=refer_to_authority,
        query=query_response,
        classification=classification_response,
        transaction=transaction_response,
    )


def run_ingest_pipeline(force: bool = False) -> None:
    """Parse the corpus into settings.output_dir, then embed whatever is there.

    Parsing is expensive, so it is skipped unless the output dir holds no parsed
    page JSON yet, or force=True.
    """
    output_dir = Path(settings.output_dir)

    if force or not any(output_dir.rglob("*.json")):
        SOURCES = ["track2_data/control_lists", "track2_data/legislation"]
        run_parse(SOURCES, Path(settings.corpus_dir), output_dir)

    # Each directory holding parsed page JSON becomes one collection.
    parsed_dirs = [
        d for d in sorted(output_dir.rglob("*")) if d.is_dir() and any(d.glob("*.json"))
    ]
    run_embed(parsed_dirs)


@app.post("/ingest")
def ingest(force: bool = False) -> dict:
    run_ingest_pipeline(force=force)
    return {"ok": False}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
