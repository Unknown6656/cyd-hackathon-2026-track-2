"""Track 2 export control advisor — minimal skeleton. Implement your advisor here.

See README.md for the full contract (request blocks, response shape, citations).
"""

import os

from fastapi import FastAPI

from .models import *
from .config import Settings

config = Settings()


app = FastAPI(title="Track 2 export control advisor")

# The data is mounted read-only at /corpus:
#   legislation/    20 PDFs   KMG, KMV, GKG, GKV, EmbG in de/fr/it/en
#   control_lists/   6 PDFs   dual-use list and Annex 3, de/fr/it only
#   parties/        public_sanctions.json, internal_flagged.json
CORPUS_DIR = os.environ.get("CORPUS_DIR", "/corpus")

# Inference endpoint (OpenAI-compatible LiteLLM proxy) — see inference.env.example.
OPENAI_BASE_URL = config.openai_base_url
OPENAI_API_KEY = config.openai_api_key
MODEL = config.model



@app.post("/advise")
def advise(req: AdviseRequest) -> AdviseResponse:
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
        classification_response = AdviseClassificationResponse(
            controlled=False,
            regime=AdviseClassificationRegime.NONE,
            entries=[],
            deciding_text="TODO: not implemented",
            citations=[],
        )

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


@app.get("/health")
def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
