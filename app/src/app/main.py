"""Track 2 export control advisor — minimal skeleton. Implement your advisor here.

See README.md for the full contract (request blocks, response shape, citations).
"""

import os

from fastapi import FastAPI
from models import AdviseRequest, AdviseResponse


app = FastAPI(title="Track 2 export control advisor")

# The data is mounted read-only at /corpus:
#   legislation/    20 PDFs   KMG, KMV, GKG, GKV, EmbG in de/fr/it/en
#   control_lists/   6 PDFs   dual-use list and Annex 3, de/fr/it only
#   parties/        public_sanctions.json, internal_flagged.json
CORPUS_DIR = os.environ.get("CORPUS_DIR", "/corpus")

# Inference endpoint (OpenAI-compatible LiteLLM proxy) — see inference.env.example.
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("MODEL")






@app.post("/advise")
def advise(req: AdviseRequest) -> AdviseResponse:
    # TODO: implement your advisor.
    

    response: AdviseResponse = AdviseResponse(
        refer_to_authority=False,
        query=None,
        classification=None,
        transaction=None,
    )

    if req.query is not None:
        response.query = {"answer": "TODO: not implemented", "citations": []}

    if req.item is not None:
        response.classification = {
            "controlled": False,
            "regime": "none",          # war_materiel | specific_military | dual_use | none
            "entries": [],
            "deciding_text": "TODO: not implemented",
            "citations": [],
        }

    if req.transaction is not None:
        response.transaction = {
            # NO_LICENCE_REQUIRED | LICENCE_REQUIRED | PROHIBITED | REFER_TO_AUTHORITY
            "verdict": "REFER_TO_AUTHORITY",
            "authority": None,
            "answer": "TODO: not implemented",
            "citations": [],
        }

    return response


@app.get("/health")
def health() -> dict:
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
