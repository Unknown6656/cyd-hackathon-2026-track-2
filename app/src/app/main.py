"""Track 2 export control advisor — minimal skeleton. Implement your advisor here.

See README.md for the full contract (request blocks, response shape, citations).
"""

import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .backend import get_classification, get_transaction_assessment
from .config import settings
from .ingest import run_embed, run_parse
from .models import *

app = FastAPI(title="Track 2 export control advisor")

_STATIC_INDEX = Path(__file__).resolve().parent.parent.parent / "static" / "index.html"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the single-page advise UI."""
    return _STATIC_INDEX.read_text(encoding="utf-8")


_MODELS_TTL_SECONDS = 300
_models_cache: list[str] | None = None
_models_cache_at: float = 0.0


async def list_available_models() -> list[str] | None:
    """Return the model IDs offered by the litellm endpoint, or None if the
    endpoint cannot be reached. Cached for a short TTL."""
    global _models_cache, _models_cache_at
    if _models_cache is not None and time.monotonic() - _models_cache_at < _MODELS_TTL_SECONDS:
        return _models_cache
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.openai_base_url}/models",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            )
            response.raise_for_status()
        _models_cache = [m["id"] for m in response.json()["data"] if m["owned_by"] == "openai" and "mode" not in m.keys()]
        _models_cache_at = time.monotonic()
        return _models_cache
    except (httpx.HTTPError, KeyError, ValueError):
        return None


@app.get("/models")
async def models() -> dict:
    model_ids = await list_available_models()
    if model_ids is None:
        raise HTTPException(status_code=502, detail="Could not reach the model endpoint")
    return {"models": model_ids, "default": settings.model}


@app.post("/advise")
async def advise(req: AdviseRequest) -> AdviseResponse:
    if req.model_name is not None:
        available = await list_available_models()
        # Fail open: if the endpoint is unreachable, let the provider error
        # surface rather than blocking the request.
        if available is not None and req.model_name not in available:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model '{req.model_name}'. Available models: {available}",
            )

    refer_to_authority: bool = False
    query_response: AdviseQueryResponse | None = None
    classification_response: AdviseClassificationResponse | None = None
    transaction_response: AdviseTransactionResponse | None = None

    if req.query is not None:
        query_response = AdviseQueryResponse(
            answer="not implemented",
            citations=[]
        )

    if req.item is not None:
        classification_response = await get_classification(req.item, req.documents, req.model_name)

    if req.transaction is not None:
        if classification_response is None or req.item is None: # python is dumb
            # TODO: return error response: invalid request item missing
            raise RuntimeError("'item' missing in request")

        transaction_response = await get_transaction_assessment(
            req.item,
            req.transaction,
            classification_response,
            req.model_name,
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
    try:
        run_ingest_pipeline(force=force)
        return {"ok": True}
    except Exception:
        return {"ok": False}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
