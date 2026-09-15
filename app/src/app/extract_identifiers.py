"""Turn per-page PDF text into one record per identifier.

Input : JSON like {"file_name": ..., "pages": [{"page_number": 31, "text": ...}, ...]}
Output: JSON list  [{"identifier": "0A001", "text": "..."}, ...]

Rules
  "0A001 <text>"                       -> start of entry 0A001
  "0A001 (Fortsetzung)"                -> continuation of 0A001 (header dropped)
  "0B001b (Fortsetzung)"               -> continuation of 0B001 (item suffix dropped)
  "1C111a2 (Fortsetzung)"              -> continuation of 1C111
  "1C001 Anmerkung 1 (Fortsetzung)"    -> continuation of 1C001
  "0B <text>" / "ANHANG ..." / title   -> section header, skipped
  page with no header (PDF header lost) -> body keeps flowing into the previous entry
Everything else is appended to the text of the current entry.

Usage: python3 extract_identifiers.py [input.json] [output.json]
"""

import json
import re
import sys
from dataclasses import dataclass

ID = r"\d[A-Z]\d{3}"  # e.g. 0A001

# entry header: "0A001 <text>" - the code must not run into more letters/digits,
# otherwise in-body cross references ("siehe 0A001e", "Anmerkung: 0A001i erfasst ...")
# would look like the start of a new entry
RE_NEW = re.compile(rf"^({ID})(?![0-9A-Za-z])\s+\S")
# continuation header: "0A001 (Fortsetzung)", "0B001b (Fortsetzung)",
# "1C111a2 (Fortsetzung)", "1C001 Anmerkung 1 (Fortsetzung)" -> base code only
RE_CONT = re.compile(rf"^({ID})(?![0-9]).*\(\s*Fortsetzung\s*\)\s*$", re.IGNORECASE)
RE_CATEGORY = re.compile(r"^\d[A-Z]\s")  # category header, e.g. "0B Prüf-, Test-..."


@dataclass
class IdentifierDescription:
    identifier: str
    description: str


def extract(pages: list[dict]) -> list[IdentifierDescription]:
    #inp = sys.argv[1] if len(sys.argv) > 1 else "example-output.json"
    #out = sys.argv[2] if len(sys.argv) > 2 else "output.json"

    #with open(inp, encoding="utf-8") as fh:
    #    pages = json.load(fh)["pages"]

    entries: dict[str, list[str]] = {}  # identifier -> lines, in order of first appearance
    current = None

    for page in sorted(pages, key=lambda p: p["page_number"]):
        for line in page["text"].splitlines():
            line = re.sub(r"[ \t]+", " ", line).strip()

            cont = RE_CONT.match(line)
            if cont:  # continuation header -> same entry, letter suffix dropped
                current = cont.group(1)
                continue

            new = RE_NEW.match(line)
            if new:  # new entry
                current = new.group(1)
                if current not in entries:  # a repeated header is noise, not a new entry
                    entries[current] = [line]
                continue

            if not line or RE_CATEGORY.match(line):
                continue  # blank line or category header

            if current:
                entries[current].append(line)
            # else: document/section preamble before the first entry -> ignored

    result = [
        IdentifierDescription(identifier=k, description="\n".join(v))
        for k, v in entries.items()
    ]

    # sanity: no header line may survive into a text
    #for e in result:
    #    assert "Fortsetzung)" not in e["text"], e["identifier"]

    #with open(out, "w", encoding="utf-8") as fh:
    #    json.dump(result, fh, ensure_ascii=False, indent=2)

    #print(f"{len(result)} entries -> {out}")
    #for e in result:
    #    print(f"  {e['identifier']}: {len(e['text'])} chars")

    return result
