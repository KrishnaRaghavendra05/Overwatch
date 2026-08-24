# Overwatch

Satellite land-cover change detection agent with human-gated report filing, built for the TrueForge Agent Harness Hackathon.

---

## Architecture

Three layers, hard boundaries between them:

- **`core/`** — pure Python + numpy. NDVI/NDWI math, cloud masking, threshold logic. Zero knowledge of TrueForge, MCP, or any agent framework. Tested and reviewable in isolation. This is the math you trust.
- **`agent/`** — harness-facing code. Fetches imagery via MCP tool calls, runs three parallel verification subagents, holds the approval-gate workflow. Calls into `core/`. Never the other way round.
- **`dashboard/`** — write-back target. FastAPI + SQLite + Jinja2. The agent writes approved/retracted reports here through one function (`dashboard/write.py`). No inline SQL anywhere else. A human can watch this page update in real time on approval.

Why split this way: the math (`core/`) must be reviewable and testable without spinning up a harness. The write-path (`dashboard/write.py`) must be reachable only through the approval gate — structurally, not just by convention.

---

## Ten-step workflow

1. **Trigger** — plain-English query or scheduled check
2. **Fetch imagery** — MCP tool call to imagery API (Planetary Computer STAC)
3. **Compute raw signal** — NDVI or NDWI delta, run in Daytona sandbox
4. **Verify in parallel** — three subagents try to disprove the signal: cloud/shadow check, weather cross-check, threshold test
5. **Draft report** — only if all three checks pass
6. **Human approval gate** — agent stops and presents; nothing files without explicit approval
7. **Write to dashboard** — approved flag written to live tracking system
8. **Verify write** — agent reads back the record to confirm it landed correctly
9. **Retraction path** — if later evidence contradicts an approved flag, agent proposes retraction behind a fresh approval gate
10. **Escalation** *(optional, Phase 6)* — notify if approved flag sits unreviewed too long

---

## Setup

```bash
# Clone and create venv
git clone <repo-url>
cd geo-change-agent
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Install
pip install -e ".[dev]"

# Configure
copy .env.example .env
# Fill in keys: MODEL_PROVIDER, MODEL_API_KEY, DAYTONA_API_KEY,
#               IMAGERY_PROVIDER_KEY, IMAGERY_PROVIDER_URL,
#               CACHE_DIR, DASHBOARD_DB_PATH

# Run TrueForge locally
# (see TrueForge docs: github.com/truefoundry/trueforge)

# Run the dashboard
uvicorn dashboard.app:app --reload

# Run tests
pytest
ruff check .
```

---

## Demo

<!-- TODO Phase 6: embed demo video link here -->

---

## Judging criteria mapping

| Criterion | Where it shows |
|---|---|
| Potential impact | Agricultural-insurance framing: agent gates a real-money claim decision |
| Creativity | Geospatial/remote-sensing agents rare at this hackathon |
| Technical excellence | Deterministic index pipeline; write/verify/retract loop |
| Use of sponsor tools | MCP tool call, Daytona sandbox, human-approval pause, subagent delegation, Qodo PR trail |
| Control & safety | Two real gates: Step 6 (file) and Step 9 (retract), both with real stakes |
| Presentation | Before/after imagery + dashboard update visible in demo video |

---

## AI tool disclosure

<!-- TODO: fill this in truthfully before submission.
     List which tool was used for which part of the codebase.
     This section is required by hackathon rules.
     Do not fabricate — only disclose what actually happened. -->
