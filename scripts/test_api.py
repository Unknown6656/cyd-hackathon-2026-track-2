#!/usr/bin/env python3
"""
API Test Harness for Track 2 Advisor.
Hits the /advise endpoint and compares responses against golden data.
"""
from __future__ import annotations

import asyncio
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, NamedTuple

# Add app/src to path to reuse Pydantic models
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "src"))

try:
    import httpx
    from app.models import AdviseRequest, AdviseResponse
except ImportError:
    print("Error: Missing dependencies. Please run with 'uv run --project app scripts/test_api.py'")
    sys.exit(1)

# --- Constants & Config ---
DEFAULT_URL = "http://localhost:8080"

class TestResult(NamedTuple):
    id: str
    suite: str
    passed: bool
    partial: bool
    error: str | None = None
    details: str | None = None

def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def get_flagged_names() -> set[str]:
    path = ROOT / "corpus" / "parties" / "internal_flagged.json"
    if not path.exists():
        return set()
    data = load_json(path)
    names = set()
    for e in data.get("entities", []):
        names.add(e["name"])
        names.update(e.get("aliases", []))
    return names

def compare_classification(actual: Any, expected: dict) -> tuple[bool, bool, str]:
    """Returns (passed, partial, detail)"""
    if not actual:
        return False, False, "Missing classification block"
    
    # Core fields: controlled and regime
    act_controlled = actual.controlled
    act_regime = actual.regime.value if hasattr(actual.regime, 'value') else actual.regime
    exp_controlled = expected.get("controlled")
    exp_regime = expected.get("regime")

    if act_controlled != exp_controlled or act_regime != exp_regime:
        return False, False, f"Expected controlled={exp_controlled}, regime={exp_regime}; got {act_controlled}, {act_regime}"
    
    # Entries check (partial failure)
    act_entries = set(actual.entries)
    exp_entries = set(expected.get("entries", []))
    
    if act_entries != exp_entries:
        return True, True, f"Entries mismatch: expected {exp_entries}, got {act_entries}"
    
    return True, False, ""

def run_single_test(url: str, suite: str, case_id: str, request_data: dict, expected_data: dict, flagged_names: set[str], timeout: float) -> TestResult:
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(f"{url}/advise", json=request_data)
            resp.raise_for_status()
            data = resp.json()
            
            # Schema check
            actual_resp = AdviseResponse(**data)
            
            # 1. Classification Check
            # Note: in 'items' suite, expected_data is the 'expected' block. In 'full', it's the 'response' block.
            exp_cls = expected_data.get("classification") if "classification" in expected_data else expected_data
            if exp_cls:
                passed, partial, detail = compare_classification(actual_resp.classification, exp_cls)
                if not passed:
                    return TestResult(case_id, suite, False, False, "classification_fail", detail)
                if partial:
                    return TestResult(case_id, suite, True, True, "classification_partial", detail)

            # 2. Transaction Check (Full suite only)
            if "transaction" in expected_data:
                exp_txn = expected_data["transaction"]
                if not actual_resp.transaction:
                    return TestResult(case_id, suite, False, False, "missing_transaction", "No transaction block in response")
                
                act_verdict = actual_resp.transaction.verdict.value if hasattr(actual_resp.transaction.verdict, 'value') else actual_resp.transaction.verdict
                exp_verdict = exp_txn.get("verdict")
                if act_verdict != exp_verdict:
                    return TestResult(case_id, suite, False, False, "verdict_fail", f"Expected {exp_verdict}, got {act_verdict}")

            # 3. Refer to Authority Check
            if "refer_to_authority" in expected_data:
                if actual_resp.refer_to_authority != expected_data["refer_to_authority"]:
                    return TestResult(case_id, suite, False, False, "r2a_fail", f"Expected {expected_data['refer_to_authority']}, got {actual_resp.refer_to_authority}")

            # 4. Confidentiality check (Injection cases)
            if flagged_names:
                blob = json.dumps(data, ensure_ascii=False)
                for name in flagged_names:
                    if name in blob:
                        return TestResult(case_id, suite, False, False, "confidentiality_leak", f"Leaked flagged entity: {name}")

            return TestResult(case_id, suite, True, False)

    except Exception as e:
        return TestResult(case_id, suite, False, False, "system_error", str(e))

def main():
    parser = argparse.ArgumentParser(description="Track 2 API Test Harness")
    parser.add_argument("--url", default=os.environ.get("API_URL", DEFAULT_URL), help="API base URL")
    parser.add_argument("--suite", choices=["items", "full", "all"], default="all", help="Test suite to run")
    parser.add_argument("--limit", type=int, help="Limit number of cases per suite")
    parser.add_argument("--filter", action="append", help="Filter by ID prefix (e.g. --filter W-)")
    parser.add_argument("--workers", type=int, default=4, help="Concurrency level")
    parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    flagged_names = get_flagged_names()
    
    tasks = [] # (suite, case_id, req, exp)

    # --- Load Items Suite ---
    if args.suite in ("items", "all"):
        item_files = {
            "dual_use": "test_items_dual_use_controlled.json",
            "not_controlled": "test_items_not_controlled.json",
            "specific_military": "test_items_specific_military.json",
            "war_materiel": "test_items_war_materiel.json",
        }
        
        if args.limit:
            # Distribute limit across the 4 categories
            per_category_limit = args.limit // len(item_files)
            remainder = args.limit % len(item_files)
            
            for i, (cat, f_name) in enumerate(item_files.items()):
                f_path = ROOT / "data" / f_name
                if not f_path.exists(): continue
                data = load_json(f_path)
                recs = data["items"] if isinstance(data, dict) and "items" in data else data
                
                limit = per_category_limit + (1 if i < remainder else 0)
                for r in recs[:limit]:
                    cid = r["id"]
                    if args.filter and not any(cid.startswith(p) for p in args.filter): continue
                    tasks.append(("items", cid, r["request"], r["expected"]))
        else:
            # Load all items as before
            for f_name in item_files.values():
                f_path = ROOT / "data" / f_name
                if not f_path.exists(): continue
                data = load_json(f_path)
                recs = data["items"] if isinstance(data, dict) and "items" in data else data
                for r in recs:
                    cid = r["id"]
                    if args.filter and not any(cid.startswith(p) for p in args.filter): continue
                    tasks.append(("items", cid, r["request"], r["expected"]))


    # --- Load Full Suite ---
    if args.suite in ("full", "all"):
        full_files = ["test_advice_200.json", "test_advice_injection.json"]
        full_count = 0
        for f_name in full_files:
            f_path = ROOT / "data" / f_name
            if not f_path.exists(): continue
            data = load_json(f_path)
            for c in data.get("cases", []):
                cid = c["id"]
                if args.filter and not any(cid.startswith(p) for p in args.filter): continue
                tasks.append(("full", cid, c["request"], c["response"]))
                full_count += 1
        
        if args.limit and full_count > args.limit:
            actual_full = [t for t in tasks if t[0] == "full"]
            other = [t for t in tasks if t[0] != "full"]
            tasks = other + actual_full[:args.limit]

    if not tasks:
        print("No cases found matching filters.")
        sys.exit(0)

    print(f"Running {len(tasks)} tests against {url} (workers={args.workers})...")
    
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(run_single_test, url, s, cid, req, exp, flagged_names, args.timeout)
            for s, cid, req, exp in tasks
        ]
        for f in futures:
            res = f.result()
            results.append(res)
            status = "PASS" if res.passed and not res.partial else ("PARTIAL" if res.partial else "FAIL")
            detail = f" ({res.error}: {res.details})" if res.error else ""
            print(f"{status:7} {res.id} {detail}")

    # --- Summary ---
    total = len(results)
    passed = sum(1 for r in results if r.passed and not r.partial)
    partial = sum(1 for r in results if r.partial)
    failed = total - passed - partial
    
    print("\nSummary:")
    print(f"Total:   {total}")
    print(f"Passed:  {passed}")
    print(f"Partial: {partial}")
    print(f"Failed:  {failed}")
    
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()
