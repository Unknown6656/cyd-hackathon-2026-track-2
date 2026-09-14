import json
import logging
import re
import sys
from pathlib import Path

from docling_core.types.doc import BaseMeta, DoclingDocument, SectionHeaderItem, TableItem, TextItem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("pdf_split")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INPUT_DIR = PROJECT_ROOT / "parsed_data" / "control_lists"
OUTPUT_DIR = PROJECT_ROOT / "parsed_data" / "products"

# Control codes: EKN-style "3A001" (digit, letter, 3 digits) + optional letter suffix ("3A001a"),
# plus UN-military-list codes "ML1".."ML22"
PRODUCT_CODE_RE = re.compile(r"\b(?:\d[A-Za-z]\d{3}[A-Za-z]?|ML\d{1,2})\b")


def iter_blocks(doc: DoclingDocument):
    """Yield (item, kind, level, text) in document order, skipping furniture."""
    for item, _ in doc.iterate_items():
        if isinstance(item, SectionHeaderItem):
            text = item.text.strip()
            if text:
                yield item, "heading", item.level, text
        elif isinstance(item, TableItem):
            yield item, "table", None, item.export_to_markdown(doc=doc).strip()
        elif isinstance(item, TextItem):
            text = item.text.strip()
            if text:
                yield item, item.label.value, None, text


def tag_item(item, related_code: str | None, headings: list[str], codes: list[str]) -> None:
    meta = {}
    if related_code:
        meta["app__product_code"] = related_code
    if headings:
        meta["app__heading_path"] = " / ".join(headings)
    if codes:
        meta["app__codes"] = ",".join(codes)
    if meta:
        current = item.meta.model_dump(exclude_none=True) if isinstance(item.meta, BaseMeta) else {}
        current.update(meta)
        item.meta = BaseMeta(**current)


def split_document(doc: DoclingDocument) -> dict:
    headings: list[tuple[int, str]] = []
    active_code: str | None = None
    blocks: list[dict] = []

    for item, kind, level, text in iter_blocks(doc):
        codes = list(dict.fromkeys(PRODUCT_CODE_RE.findall(text)))
        if kind == "heading":
            level = level or 1
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, text))
            if codes:
                active_code = codes[0]
            tag_item(item, codes[0] if codes else None, [t for _, t in headings], codes)
            continue

        own_codes = codes
        inherited = active_code is not None and active_code not in own_codes
        related_code = own_codes[0] if own_codes else active_code
        tag_item(item, related_code, [t for _, t in headings], own_codes)
        blocks.append(
            {
                "type": kind,
                "heading_path": [t for _, t in headings],
                "codes": own_codes,
                "related_code": related_code,
                "inherited": inherited,
                "text": text,
            }
        )
        if len(own_codes) == 1:
            active_code = own_codes[0]

    products: dict[str, dict] = {}
    unassigned: list[dict] = []
    for b in blocks:
        if not b["related_code"]:
            unassigned.append(b)
            continue
        p = products.setdefault(
            b["related_code"],
            {"code": b["related_code"], "heading_paths": [], "blocks": []},
        )
        if b["heading_path"] and b["heading_path"] not in p["heading_paths"]:
            p["heading_paths"].append(b["heading_path"])
        p["blocks"].append(b)

    return {
        "products": [products[c] for c in sorted(products)],
        "unassigned": unassigned,
        "num_products": len(products),
        "num_blocks": len(blocks),
    }


def to_tagged_markdown(doc: DoclingDocument) -> str:
    """Render the doc as markdown with one HTML comment of tags per block."""
    lines: list[str] = []
    for item, kind, level, text in iter_blocks(doc):
        meta = item.meta
        code = getattr(meta, "app__product_code", None) if meta else None
        if code:
            path = getattr(meta, "app__heading_path", None)
            lines.append(f"<!-- code:{code}" + (f" section:{path}" if path else "") + " -->")
        if kind == "heading":
            lines.append("#" * (level or 1) + " " + text.rstrip())
        else:
            lines.append(text)
        lines.append("")
    return "\n".join(lines)


def split_file(json_path: Path) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    doc = DoclingDocument.model_validate(data)
    result = split_document(doc)
    result["source"] = json_path.name
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{json_path.stem}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    tagged_path = OUTPUT_DIR / f"{json_path.stem}.tagged.json"
    tagged_path.write_text(
        json.dumps(doc.export_to_dict(), ensure_ascii=False), encoding="utf-8"
    )
    tagged_md_path = OUTPUT_DIR / f"{json_path.stem}.tagged.md"
    tagged_md_path.write_text(to_tagged_markdown(doc), encoding="utf-8")
    logger.info(
        "Wrote %s (%d products, %d blocks, %d unassigned) + %s + %s",
        out_path, result["num_products"], result["num_blocks"],
        len(result["unassigned"]), tagged_path, tagged_md_path,
    )
    return result


def main() -> int:
    if not INPUT_DIR.is_dir():
        logger.error("Input directory %s does not exist", INPUT_DIR)
        return 1

    json_files = sorted(p for p in INPUT_DIR.glob("*.json"))
    if not json_files:
        logger.warning("No JSON files found in %s", INPUT_DIR)
        return 0

    failures = 0
    for i, path in enumerate(json_files, start=1):
        logger.info("(%d/%d) Splitting %s", i, len(json_files), path.name)
        try:
            split_file(path)
        except Exception:
            failures += 1
            logger.exception("Failed to split %s", path)

    logger.info("Done: %d converted, %d failed", len(json_files) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
