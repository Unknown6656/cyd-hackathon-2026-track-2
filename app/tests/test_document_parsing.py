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
INPUT_DIR = REPO_ROOT / "corpus" / "track2_data" / "control_lists"


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


def test_parse_writes_one_json_per_file(parsed) -> None:
    _pdf, output_dir = parsed
    files = sorted(output_dir.glob("*.json"))
    assert files, "expected at least one JSON file"
    assert len(files) == 1, "expected exactly one JSON file per PDF"


def test_page_json_uses_original_filename(parsed) -> None:
    pdf, output_dir = parsed
    for path in output_dir.glob("*.json"):
        assert path.name == f"{pdf.stem}.json"


def test_page_json_has_expected_fields(parsed) -> None:
    pdf, output_dir = parsed
    for path in output_dir.glob("*.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        assert rec["file_name"] == pdf.name
        assert rec["file_hash"] == _filename_hash(pdf.name)
        assert isinstance(rec["pages"], list)
        assert rec["pages"]
        for page in rec["pages"]:
            assert isinstance(page["page_number"], int)
            assert page["page_number"] >= 1
            assert isinstance(page["text"], str)
            assert page["text"].strip()


def test_page_numbers_are_unique(parsed) -> None:
    _pdf, output_dir = parsed
    for path in output_dir.glob("*.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        page_numbers = [p["page_number"] for p in rec["pages"]]
        assert len(page_numbers) == len(set(page_numbers))


@pytest.fixture()
def collection_name():
    name = f"pytest-docs-{uuid.uuid4().hex[:12]}"
    yield name
    db = VectorDB(settings.qdrant_url, None)
    if db.client.collection_exists(name):
        db.delete_collection(name)


@pytest.fixture()
def embed_input(parsed, tmp_path):
    """Copy a small subset of parsed pages to keep embedding calls cheap."""
    pdf, output_dir = parsed
    jsons = sorted(output_dir.glob("*.json"))
    assert jsons

    subset = tmp_path / "embed_input"
    subset.mkdir()
    n_pages = 0
    for path in jsons:
        if n_pages >= 3:
            break
        rec = json.loads(path.read_text(encoding="utf-8"))
        keep = rec["pages"][: 3 - n_pages]
        n_pages += len(keep)
        out = subset / path.name
        out.write_text(
            json.dumps({**rec, "pages": keep}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return pdf, subset, n_pages



def test_embed_documents_writes_vectors(embed_input, collection_name) -> None:
    pdf, subset_dir, n_pages = embed_input
    parser = DocumentProcessor(collection_name, subset_dir)

    asyncio.run(parser.embed_documents(sorted(subset_dir.glob("*.json"))))

    points, _ = parser.vector_db.client.scroll(
        collection_name,
        limit=n_pages,
        with_payload=True,
        with_vectors=False,
    )
    assert len(points) == n_pages
    for point in points:
        assert point.payload["file_name"] == pdf.name
        assert point.payload["file_hash"] == _filename_hash(pdf.name)
        assert isinstance(point.payload["page_number"], int)
        assert point.payload["text"].strip()
