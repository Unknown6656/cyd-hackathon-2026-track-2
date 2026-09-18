# Final Presentation — Track 2 Export Control Advisor

Working folder for the final presentation. All presentation data lives here;
nothing outside `presentation/` should be touched for this purpose.

## Contents

| File | What it is |
|---|---|
| `index.html` | The deck (reveal.js, self-contained, no external assets) — open in a browser |
| `outline.md` | Slide-by-slide description of the current deck (source of truth) |
| `facts.md` | Verified numbers and facts used on slides (corpus size, test suites, stack, etc.) |
| `architecture.mmd` | Mermaid diagrams (system + request lifecycle), updated to match the **current** code |
| `gaps-and-qa.md` | Known gaps, mitigations, and likely judge questions — **Q&A prep only, not in the deck** |
| `demo-script.md` | Optional live demo / curl walkthrough — **not in the deck** (demo slide was cut); use if you get time |
| `logo.jpg` | Team logo (from repo root), shown on the title and thank-you slides |

## Status

- [x] Codebase reviewed (main @ `7273d44`)
- [x] Deck built as `index.html` (10 slides, no speaker notes) — see `outline.md`
- [x] Model name: Qwen/Qwen3.8-Flash-Next (per request)
- [ ] (Optional) Run the test suite against the deployed endpoint and keep the numbers ready for Q&A; save output to `results/`
- [ ] Update `doc/ARCHITECTURE.md` in the repo — it is **out of date** (see `gaps-and-qa.md`)

## Key message (elevator pitch)

> A RAG + multi-agent advisor that classifies items against Swiss war materiel
> and dual-use control lists, rules on licensing per transaction, screens
> counterparties against a confidential flagged list it can never disclose —
> and grounds every answer in cited legal text, not model memory.
