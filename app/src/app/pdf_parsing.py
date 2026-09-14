import json
import logging
import sys
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("pdf_parsing_assistant")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INPUT_DIR = PROJECT_ROOT / "data" / "track2_data" / "control_lists" 
OUTPUT_DIR = PROJECT_ROOT / "parsed_data" / "control_lists"

def parse_pdf(converter: DocumentConverter, pdf_path: Path) -> None:
    result = converter.convert(str(pdf_path))
    doc = result.document

    md_path = OUTPUT_DIR / f"{pdf_path.stem}.md"
    md_path.write_text(doc.export_to_markdown(), encoding="utf-8")

    json_path = OUTPUT_DIR / f"{pdf_path.stem}.json"
    json_path.write_text(json.dumps(doc.export_to_dict(), ensure_ascii=False), encoding="utf-8")

    logger.info("Wrote %s and %s", md_path, json_path)


def main() -> int:
    if not INPUT_DIR.is_dir():
        logger.error("Input directory %s does not exist", INPUT_DIR)
        return 1

    pdf_files = sorted(
        p for p in INPUT_DIR.rglob("*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".PDF"}
    )
    if not pdf_files:
        logger.warning("No PDF files found in %s", INPUT_DIR)
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF])

    total = len(pdf_files)
    failures = 0
    for i, pdf_path in enumerate(pdf_files, start=1):
        logger.info("(%d/%d) Converting %s", i, total, pdf_path)
        try:
            parse_pdf(converter, pdf_path)
        except Exception:
            failures += 1
            logger.exception("Failed to convert %s", pdf_path)

    logger.info("Done: %d converted, %d failed", total - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
