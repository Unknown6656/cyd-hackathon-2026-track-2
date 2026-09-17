# Final Presentation — Track 2 Export Control Advisor

Working folder for the final presentation. All presentation data lives here;
nothing outside `presentation/` should be touched for this purpose.

## Contents

| File | What it is |
|---|---|
| `outline.md` | Suggested slide-by-slide deck structure with speaker notes (the main proposal) |
| `facts.md` | Verified numbers and facts to put on slides (corpus size, test suites, stack, etc.) |
| `architecture.mmd` | Mermaid diagrams (system + request lifecycle), updated to match the **current** code |
| `gaps-and-qa.md` | Honest known gaps, mitigations, and likely judge questions with suggested answers |
| `demo-script.md` | Suggested live demo / curl walkthrough for the talk |

## Status

- [x] Codebase reviewed (main @ `7273d44`)
- [x] Deck outline drafted
- [ ] Fill in live test-suite results → add `results/` once we run `scripts/test_api.py` against the deployed endpoint
- [ ] Pick a deck format (reveal.js / Marp / slides.com) and render `outline.md`
- [ ] Update `doc/ARCHITECTURE.md` in the repo — it is **out of date** (see `gaps-and-qa.md`)

## Key message (elevator pitch)

> A RAG + multi-agent advisor that classifies items against Swiss war materiel
> and dual-use control lists, rules on licensing per transaction, screens
> counterparties against a confidential flagged list it can never disclose —
> and grounds every answer in cited legal text, not model memory.
