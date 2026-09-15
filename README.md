# Track 2 — application template

Starter skeleton for the Track 2 export control advisor. Read the scenario, the data description, the full I/O contract and the submission rules on the website:
<https://hackathon-armasuisse.github.io/tracks/track-2/>

This template uses FastAPI and Uvicorn as a simple starting point, for more information see this [description](https://www.geeksforgeeks.org/python/fastapi-uvicorn/). We note that usage of this template is **optional**. You can start from scratch or use your own framework, as long as you meet the requirements.

## What's here

- `app/main.py` — the `/advise` endpoint skeleton; implement your advisor here.
- `inference.env.example` — the inference endpoint variables we pass at deploy.
- `Dockerfile` — builds and runs the app on port 8080.
- `compose.yaml` — runs the app behind a TLS-terminating reverse proxy.
- `Caddyfile` — the reverse proxy configuration, replace `N` with your team number.

The legal sources and the party lists are distributed separately as an encrypted zip, please see the website.

## Testing
The project includes an API test harness to validate the `/advise` endpoint against golden test cases.

### Running the API Tests
There is a provided flake to enter the development environment if you use nix:
```bash
nix develop
```

Once in the shell, you can run tests using `uv`:
```bash
# Run a small set of 8 item-only tests (local)
uv run --project app scripts/test_api.py --suite items --limit 8

# Run the full suite (items + advice cases)
uv run --project app scripts/test_api.py --suite all

# Run tests against a deployed endpoint
uv run --project app scripts/test_api.py --url https://llmhack-team-N.hackathon.intlab.ch

# Filter tests by ID prefix (e.g., only War Materiel)
uv run --project app scripts/test_api.py --suite items --filter W-
```

### Test Suites
- `items`: Validates basic classification using `data/test_items_*.json`.
- `full`: Validates full transaction advice and prompt-injection resistance using `data/test_advice_200.json` and `data/test_advice_injection.json`.

**Note:** Core classification (`controlled`, `regime`) must match exactly for a PASS. Mismatches in specific law `entries` result in a **PARTIAL** status.

## Deploying on your team VM

Your VM already has a TLS certificate and a public hostname,
`llmhack-team-N.hackathon.intlab.ch`. `compose.yaml` in this repository runs two
containers: **Caddy**, which terminates TLS on that hostname, and **your app**,
which Caddy reaches at `app:8080` on the internal network. Before starting to build, do the following two steps:

1. Copy `inference.env.example` to `inference.env` and fill in the values for your team.
2. In the `Caddyfile`, replace `N` with your team number.
