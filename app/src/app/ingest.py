from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from .config import Settings
from .documents import DocumentProcessor
from .vector_db import VectorDB

settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("ingest")
SOURCES = ["track2_data/control_lists", "track2_data/legislation"]

def run_parse(sources: list[str], data_root: Path, parsed_root: Path) -> int:
    """Parse each source's PDFs into one JSON per file. No Qdrant or embedding
    here, so this can run on a machine with plenty of RAM."""
    rc = 0
    for src in sources:
        data_dir = data_root / src
        parsed_dir = parsed_root / src
        if not data_dir.is_dir():
            logger.error("parse: source dir %s does not exist; skipping", data_dir)
            rc = 1
            continue
        DocumentProcessor(src, parsed_dir).parse_pdfs(data_dir)
        logger.info("parse: %s done", src)
    return rc


def run_embed(parsed_dirs: list[Path]) -> int:

    db = VectorDB(settings.qdrant_url, None)

    rc = 0
    for parsed_dir in parsed_dirs:
        collection = parsed_dir.name
        if not parsed_dir.is_dir():
            logger.error("embed: parsed dir %s does not exist; skipping", parsed_dir)
            rc = 1
            continue
        json_paths = sorted(parsed_dir.glob("*.json"))
        if not json_paths:
            logger.error("embed: no JSON files found in %s; skipping", parsed_dir)
            rc = 1
            continue
        if db.client.collection_exists(collection):
            db.delete_collection(collection)
        logger.info(
            "embed: ingesting %d file(s) from %s into collection '%s' ...",
            len(json_paths),
            parsed_dir,
            collection,
        )
        asyncio.run(DocumentProcessor(collection, parsed_dir).embed_documents(json_paths))
        logger.info("embed: %s done", collection)
    return rc


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"parse", "embed"}:
        logger.error("usage: python -m app.ingest parse | embed <parsed-dir> [more...]")
        return 2
    verb = sys.argv[1]

    if verb == "parse":
        return run_parse(
            SOURCES,
            Path(settings.corpus_dir),
            Path(settings.output_dir),
        )

    paths = [Path(p) for p in sys.argv[2:]]
    if not paths:
        logger.error("embed: specify at least one parsed dir to embed")
        return 2
    return run_embed(paths)


if __name__ == "__main__":
    raise SystemExit(main())
