import asyncio
import json
import shutil
import uuid
from pathlib import Path

import pytest

from app.config import settings
from app.documents import DocumentProcessor, _filename_hash
from app.vector_db import VectorDB

# Tests run from the `app/` package; the PDF sources live at the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "data" / "track2_data" / "control_lists"


@pytest.fixture(scope="module")
def parsed(tmp_path_factory):
    """Parse a single control-list PDF into a temp dir; return (pdf, output_dir)."""
    if not INPUT_DIR.is_dir():
        pytest.skip(f"input data not found at {INPUT_DIR}")
    pdfs = sorted(INPUT_DIR.rglob("*.pdf"))
    if not pdfs:
        pytest.skip(f"no PDF files found in {INPUT_DIR}")

    input_dir = tmp_path_factory.mktemp("input")
    shutil.copy(pdfs[0], input_dir)

    output_dir = tmp_path_factory.mktemp("output")
    DocumentProcessor("control_lists", output_dir).parse_pdfs(input_dir)

    return pdfs[0], output_dir


def test_parse_writes_page_json_files(parsed) -> None:
    _pdf, output_dir = parsed
    files = sorted(output_dir.glob("*.json"))
    assert files, "expected at least one page JSON file"


def test_page_json_filename_encodes_hash_and_page(parsed) -> None:
    _pdf, output_dir = parsed
    for path in output_dir.glob("*.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        assert path.name == f"{rec['file_hash']}_{rec['page_number']}.json"
        assert path.name == f"{_filename_hash(rec['file_name'])}_{rec['page_number']}.json"


def test_page_json_has_expected_fields(parsed) -> None:
    pdf, output_dir = parsed
    for path in output_dir.glob("*.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        assert rec["file_name"] == pdf.name
        assert rec["file_hash"] == _filename_hash(pdf.name)
        assert isinstance(rec["page_number"], int)
        assert rec["page_number"] >= 1
        assert isinstance(rec["text"], str)
        assert rec["text"].strip()


def test_page_numbers_are_unique(parsed) -> None:
    _pdf, output_dir = parsed
    pages = [
        json.loads(p.read_text(encoding="utf-8"))["page_number"]
        for p in output_dir.glob("*.json")
    ]
    assert len(pages) == len(set(pages))


@pytest.fixture()
def collection_name():
    name = f"pytest-docs-{uuid.uuid4().hex[:12]}"
    yield name
    db = VectorDB(settings.qdrant_url, None)
    if db.client.collection_exists(name):
        db.delete_collection(name)


@pytest.fixture()
def embed_input(parsed, tmp_path):
    """Copy a small subset of parsed page JSONs to keep embedding calls cheap."""
    pdf, output_dir = parsed
    jsons = sorted(output_dir.glob("*.json"))
    assert jsons
    subset = tmp_path / "embed_input"
    subset.mkdir()
    for p in jsons[:3]:
        shutil.copy(p, subset)
    return pdf, subset, jsons[:3]



def test_embed_documents_writes_vectors(embed_input, collection_name) -> None:
    pdf, subset_dir, subset_jsons = embed_input
    parser = DocumentProcessor(collection_name, subset_dir)

    asyncio.run(parser.embed_documents(subset_dir))

    points, _ = parser.vector_db.client.scroll(
        collection_name,
        limit=len(subset_jsons),
        with_payload=True,
        with_vectors=False,
    )
    assert len(points) == len(subset_jsons)
    for point in points:
        assert point.payload["file_name"] == pdf.name
        assert point.payload["file_hash"] == _filename_hash(pdf.name)
        assert isinstance(point.payload["page_number"], int)
        assert point.payload["text"].strip()
