from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import TableItem

from .config import Settings
from .embed import EmbeddingModel
from .vector_db import VectorDB

settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def _filename_hash(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]


class DocumentProcessor:

    def __init__(self, folder_name: str, folder_output: str | Path):
        self.folder_name = folder_name
        self.folder_output = Path(folder_output)
        self.collection_name = folder_name
        self.log = logging.getLogger(__name__)
        self.vector_db = VectorDB(settings.qdrant_url, None)
        self.embedding = EmbeddingModel(
            base_url=settings.openai_base_url.rstrip("/") + "/embeddings",
            model_name=settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    def parse_pdfs(self, folder_path: str | Path) -> None:
        folder = Path(folder_path)
        if not folder.is_dir():
            self.log.error("Input directory %s does not exist", folder)
            return

        pdf_files = sorted(
            p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"
        )
        if not pdf_files:
            self.log.warning("No PDF files found in %s", folder)
            return

        self.folder_output.mkdir(parents=True, exist_ok=True)
        options = PdfPipelineOptions()
        options.do_ocr = False
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)},
        )

        total = len(pdf_files)
        failures = 0
        for i, pdf_path in enumerate(pdf_files, start=1):
            self.log.info("(%d/%d) Parsing %s", i, total, pdf_path.name)
            try:
                self._parse_one(converter, pdf_path)
            except Exception:
                failures += 1
                self.log.exception("Failed to parse %s", pdf_path)

        self.log.info("Done: %d parsed, %d failed", total - failures, failures)

    async def embed_documents(self, json_paths: list[Path]) -> None:
        if not json_paths:
            self.log.warning("No JSON files to embed")
            return

        self.vector_db.create_collection(self.collection_name, settings.vector_size)

        for i, json_path in enumerate(json_paths, start=1):
            record = json.loads(json_path.read_text(encoding="utf-8"))
            for page in record.get("pages", []):
                text = page.get("text", "")
                if not text.strip():
                    self.log.warning(
                        "Skipping page %s in %s (empty text)",
                        page.get("page_number"),
                        json_path.name,
                    )
                    continue

                vector = await self.embedding.embed(text)
                payload = {
                    "file_name": record.get("file_name"),
                    "file_hash": record.get("file_hash"),
                    "page_number": page.get("page_number"),
                    "text": text,
                }
                self.vector_db.add_vector(vector, payload, self.collection_name)
            self.log.info("(%d/%d) Embedded %s", i, len(json_paths), json_path.name)

    def _parse_one(self, converter: DocumentConverter, pdf_path: Path) -> None:
        result = converter.convert(str(pdf_path))
        doc = result.document

        file_hash = _filename_hash(pdf_path.name)
        pages: dict[int, list[str]] = {}
        order: list[int] = []
        for page_no, text in self._iter_page_texts(doc):
            if page_no not in pages:
                pages[page_no] = []
                order.append(page_no)
            pages[page_no].append(text)

        record = {
            "file_name": pdf_path.name,
            "file_hash": file_hash,
            "pages": [
                {
                    "page_number": page_no,
                    "text": "\n\n".join(pages[page_no]),
                }
                for page_no in order
            ],
        }
        out_path = self.folder_output / f"{pdf_path.stem}.json"
        out_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        self.log.info(
            "Parsed %s -> %d page(s) to %s", pdf_path.name, len(order), self.folder_output
        )

    def _iter_page_texts(self, doc):
        for item, _level in doc.iterate_items():
            prov = getattr(item, "prov", None)
            if not prov:
                continue
            page_no = prov[0].page_no
            if isinstance(item, TableItem):
                text = item.export_to_markdown(doc=doc)
            else:
                text = getattr(item, "text", None)
            text = (text or "").strip()
            if text:
                yield page_no, text
