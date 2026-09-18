"""Smoke test that the `/` route serves the single-page advise UI.

Deliberately hermetic: no LLM, no vector DB, no running services — just that
the FastAPI app boots and returns the static page.

`app.main` transitively imports `app.agents`, which reads data files at import
time via settings, so the data/corpus dirs must point at the repo before the
import (the defaults are container paths).
"""

import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DATA_DIR", str(_REPO_ROOT / "data"))
os.environ.setdefault("CORPUS_DIR", str(_REPO_ROOT / "corpus"))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_serves_html() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "advise" in response.text
