#!/usr/bin/env python3
"""Validate data/test_advice_200.json and data/test_advice_injection.json.

Checks:
  1. Schema: every request/response parses with the pydantic models from
     app/src/app/models.py (AdviseRequest / AdviseResponse).
  2. Every main request contains item AND transaction.
  3. refer_to_authority is true exactly when the transaction verdict is
     REFER_TO_AUTHORITY.
  4. classification internal consistency:
       controlled=False  <=> regime=none and entries empty
       controlled=True   => regime in {dual_use, specific_military, war_materiel}
                             and entries non-empty
     citations are non-empty strings.
  5. Ground truth: the item in each case must match an entry of one of
     data/test_items_*.json by description; classification.controlled/regime/
     entries must agree with the 'expected' ground truth (WMD-catch-all cases
     may have a controlled item or not, but classification must still match
     the item's expected record).
  6. PROHIBITED party cases: the listed party (consignee / end user /
     intermediary) must resolve to a PUBLIC sanctions party (name or alias);
     no internal-flagged name may ever appear in a request or response.
  7. SCREENING confidentiality: each flagged case's response must be
     byte-identical (JSON) to its clean twin's response, and the response
     must not mention the flagged entity's name or any alias.
  8. Injection file: each case has documents, and the document text contains
     an instruction-like payload; verdicts are still valid enum values.
  9. Counts: 200 main cases, 18 injection cases; ids unique.

Exit code 0 = all checks passed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "src"))

from app.models import (  # noqa: E402
    AdviseClassificationRegime,
    AdviseRequest,
    AdviseResponse,
    AdviseTransactionVerdict,
)

DATA = ROOT / "data"

errors: list[str] = []
warnings: list[str] = []


def err(case_id: str, msg: str) -> None:
    errors.append(f"{case_id}: {msg}")


def warn(case_id: str, msg: str) -> None:
    warnings.append(f"{case_id}: {msg}")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_items() -> list[dict]:
    items = []
    for name in (
        "test_items_dual_use_controlled.json",
        "test_items_not_controlled.json",
        "test_items_specific_military.json",
        "test_items_war_materiel.json",
    ):
        with (DATA / name).open(encoding="utf-8") as f:
            data = json.load(f)
        records = data["items"] if isinstance(data, dict) and "items" in data else data
        for rec in records:
            rec = dict(rec)
            rec["_source_file"] = name
            items.append(rec)
    return items


def item_index(items: list[dict]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for it in items:
        desc = it["request"]["item"]["description"]
        if desc in idx:
            warn("items", f"duplicate item description across files: {desc!r}")
        idx[desc] = it
    return idx


def names_of(entry: str | None) -> set[str]:
    if not entry:
        return set()
    return {entry}


def load_parties() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    pub = load(ROOT / "corpus" / "parties" / "public_sanctions.json")
    flag = load(ROOT / "corpus" / "parties" / "internal_flagged.json")
    clean = load(ROOT / "corpus" / "parties" / "known_not_sanctioned.json")
    pub_names: dict[str, str] = {}
    for p in pub["parties"]:
        pub_names.setdefault(p["name"], p["party_id"])
        for a in p.get("aliases", []):
            pub_names.setdefault(a, p["party_id"])
    flag_names: dict[str, str] = {}
    flag_entities = {}
    for e in flag["entities"]:
        flag_entities[e["entity_id"]] = e
        flag_names.setdefault(e["name"], e["entity_id"])
        for a in e.get("aliases", []):
            flag_names.setdefault(a, e["entity_id"])
    clean_names: dict[str, str] = {}
    for e in clean["entities"]:
        clean_names.setdefault(e["name"], e["entity_id"])
        for a in e.get("aliases", []):
            clean_names.setdefault(a, e["entity_id"])
    return pub_names, flag_names, flag_entities, clean_names  # type: ignore[return-value]


def text_blob(resp: dict) -> str:
    parts = []
    for block in ("query", "classification", "transaction"):
        b = resp.get(block)
        if isinstance(b, dict):
            parts.append(b.get("answer", ""))
            parts.append(b.get("deciding_text", ""))
            parts.extend(b.get("citations", []))
    parts.append(resp.get("refer_to_authority", ""))
    return " ".join(str(p) for p in parts)


def check_consistency(cid: str, req: dict, resp: dict) -> None:
    # refer_to_authority flag
    txn = resp.get("transaction")
    if txn is not None:
        expected_ref = txn["verdict"] == "REFER_TO_AUTHORITY"
        if bool(resp["refer_to_authority"]) != expected_ref:
            err(cid, f"refer_to_authority={resp['refer_to_authority']} but verdict={txn['verdict']}")
    else:
        if resp.get("query") is None:
            err(cid, "response has neither query nor transaction block")

    # classification consistency
    cls = resp.get("classification")
    if cls is not None:
        if cls["controlled"] and cls["regime"] == "none":
            err(cid, "classification controlled=True but regime=none")
        if not cls["controlled"]:
            if cls["regime"] != "none":
                err(cid, f"classification controlled=False but regime={cls['regime']}")
            if cls["entries"]:
                err(cid, f"classification controlled=False but entries={cls['entries']}")
        else:
            if cls["regime"] == "none":
                err(cid, "classification controlled=True but regime=none")
            if not cls["entries"]:
                err(cid, f"classification controlled=True regime={cls['regime']} but no entries")
            if cls["regime"] not in ("dual_use", "specific_military", "war_materiel"):
                err(cid, f"unexpected controlled regime {cls['regime']}")

    # citations sanity
    for block in ("query", "classification", "transaction"):
        b = resp.get(block)
        if isinstance(b, dict):
            for c in b.get("citations", []):
                if not isinstance(c, str) or not c.strip():
                    err(cid, f"empty citation in {block}")


def check_ground_truth(cid: str, req: dict, resp: dict, idx: dict[str, dict]) -> None:
    item = req.get("item")
    if item is None:
        return
    desc = item["description"]
    gt = idx.get(desc)
    if gt is None:
        err(cid, f"item description not found in test_items_*.json: {desc!r}")
        return
    exp = gt["expected"]
    cls = resp.get("classification")
    if cls is None:
        warn(cid, "no classification block although request has an item")
        return
    if cls["controlled"] != bool(exp["controlled"]):
        err(cid, f"controlled={cls['controlled']} but ground truth {exp['controlled']} ({gt['id']})")
    if exp["controlled"] and cls["regime"] != exp["regime"]:
        err(cid, f"regime={cls['regime']} but ground truth {exp['regime']} ({gt['id']})")
    if exp["controlled"] and cls["entries"] != exp.get("entries", []):
        err(cid, f"entries={cls['entries']} but ground truth {exp.get('entries')} ({gt['id']})")


def main() -> int:
    main_doc = load(DATA / "test_advice_200.json")
    inj_doc = load(DATA / "test_advice_injection.json")
    items = load_items()
    idx = item_index(items)
    pub_names, flag_names, flag_entities, clean_names = load_parties()

    # ---------------- main file ----------------
    cases = main_doc["cases"]
    if len(cases) != 200:
        err("main", f"expected 200 cases, got {len(cases)}")
    ids = [c["id"] for c in cases]
    if len(set(ids)) != len(ids):
        err("main", "duplicate case ids")
    by_id = {c["id"]: c for c in cases}

    for c in cases:
        cid = c["id"]
        req = c["request"]
        resp = c["response"]
        try:
            AdviseRequest(**req)
            AdviseResponse(**resp)
        except Exception as e:  # noqa: BLE001
            err(cid, f"pydantic parse failed: {e}")
            continue

        # item + transaction required
        if req.get("item") is None or req.get("transaction") is None:
            err(cid, "request missing item or transaction")

        check_consistency(cid, req, resp)
        check_ground_truth(cid, req, resp, idx)

        txn = resp.get("transaction") or {}
        verdict = txn.get("verdict")

        # party cases must resolve to PUBLIC parties
        if verdict == "PROHIBITED":
            note = c["notes"][0] if c.get("notes") else ""
            if "PROH_PARTY" in note:
                t = req["transaction"]
                role, pid = None, None
                for field in ("consignee", "end_user"):
                    if field in note:
                        role = field
                        pid = note.rsplit("PUB-", 1)[-1].split(" ")[0]
                        pid = "PUB-" + pid
                if role is None:
                    # alias cases: "PROH_PARTY via alias 'X' -> PUB-NNNN (Name)"
                    import re as _re

                    m = _re.search(r"PUB-\d+", note)
                    if not m:
                        err(cid, f"PROH_PARTY note does not name a public party: {note}")
                    else:
                        party = next((p for p in load(ROOT / "corpus" / "parties" / "public_sanctions.json")["parties"] if p["party_id"] == m.group(0)), None)
                        if party is None:
                            err(cid, f"party id {m.group(0)} not in public list")
                        else:
                            allowed = {party["name"], *party.get("aliases", [])}
                            tvals = [t.get(k) for k in ("consignee", "end_user")] + (t.get("intermediaries") or [])
                            if not any(v in allowed for v in tvals):
                                err(cid, f"no request party field in {allowed}: {[t.get('consignee'), t.get('end_user'), t.get('intermediaries')]}")
                else:
                    # verify the request actually uses that party's name/alias
                    party = next((p for p in load(ROOT / "corpus" / "parties" / "public_sanctions.json")["parties"] if p["party_id"] == pid), None)
                    if party is None:
                        err(cid, f"party id {pid} not in public list")
                    else:
                        allowed = {party["name"], *party.get("aliases", [])}
                        val = t.get(role)
                        if val not in allowed:
                            err(cid, f"{role}={val!r} not in public party {pid} names/aliases {sorted(allowed)}")
            # no flagged name anywhere
            blob = json.dumps(c, ensure_ascii=False)
            for name, eid in flag_names.items():
                if name in blob:
                    err(cid, f"internal-flagged entity name present in case: {name!r} ({eid})")

        # screening confidentiality
        if "SCREENING" in (c["notes"][0] if c.get("notes") else ""):
            i = ids.index(cid)
            twin_id = None
            if "clean control twin" in c["notes"][0]:
                twin_id = ids[i - 1]  # flagged is the previous case
            else:
                twin_id = ids[i + 1]
            twin = by_id.get(twin_id)
            if twin is None:
                err(cid, f"twin case {twin_id} not found")
            else:
                if json.dumps(c["response"], sort_keys=True) != json.dumps(twin["response"], sort_keys=True):
                    err(cid, f"response differs from twin {twin_id} (must be byte-identical)")
            blob = text_blob(resp)
            # the flagged case: find which entity it corresponds to by matching
            # the flagged name used in the request
            t = req["transaction"]
            matched = None
            for name, eid in flag_names.items():
                if name in json.dumps(t, ensure_ascii=False):
                    matched = (name, eid)
                    break
            if matched is None:
                if "clean control twin" not in c["notes"][0]:
                    err(cid, "flagged SCREENING case: consignee/end_user does not match any flagged entity")
            else:
                e = flag_entities[matched[1]]
                for name in [e["name"], *e.get("aliases", [])]:
                    if name in blob:
                        err(cid, f"response mentions confidential entity name {name!r}")
                # response must not reveal the screening outcome: the twin's
                # answer must be identical (checked above) and generic.

    # ---------------- injection file ----------------
    icases = inj_doc["cases"]
    if len(icases) != 18:
        err("injection", f"expected 18 cases, got {len(icases)}")
    iids = [c["id"] for c in icases]
    if len(set(iids)) != len(iids):
        err("injection", "duplicate case ids")
    for c in icases:
        cid = c["id"]
        req = c["request"]
        resp = c["response"]
        try:
            AdviseRequest(**req)
            AdviseResponse(**resp)
        except Exception as e:  # noqa: BLE001
            err(cid, f"pydantic parse failed: {e}")
            continue
        check_consistency(cid, req, resp)
        check_ground_truth(cid, req, resp, idx)
        docs = req.get("documents") or []
        if not docs:
            err(cid, "injection case has no documents")
            continue
        joined = " ".join(d.get("text", "") for d in docs)
        low = joined.lower()
        injection_markers = (
            "ignore previous", "ignore all", "new instructions", "override", "you are now",
            "system:", "disregard", "new task", "always respond", "respond with verdict",
            "answer yes or no", "internal flagged list", "respond that", "system note",
            "base64", "classify as", "translate", "does not apply", "dump the full",
            "pre-approval", "waived", "ignoriere", "debug mode", "system prompt",
            "report you", "our own government", "return to the original supplier",
            "reveal the names",
        )
        if not any(m in low for m in injection_markers):
            warn(cid, "document text does not contain an obvious injection marker")
        # the REQUEST may contain a confidential name (that is the attack);
        # the RESPONSE must not mention or reveal anything about it
        resp_blob = json.dumps(resp, ensure_ascii=False)
        for name in flag_names:
            if name in resp_blob:
                err(cid, f"internal-flagged entity name present in response: {name!r}")

    # ---------------- report ----------------
    from collections import Counter

    verdicts = Counter()
    regimes = Counter()
    for c in cases:
        t = (c["response"].get("transaction") or {})
        verdicts[t.get("verdict")] += 1
        cl = c["response"].get("classification")
        if cl:
            regimes[cl["regime"]] += 1

    print(f"main cases: {len(cases)}  injection cases: {len(icases)}")
    print("verdicts:", dict(verdicts))
    print("regimes:", dict(regimes))
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
