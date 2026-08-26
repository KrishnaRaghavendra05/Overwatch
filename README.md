# Overwatch

Satellite land-cover change detection agent with human-gated report filing, built for **The Agent Harness Hackathon** (WeMakeDevs × TrueFoundry × Qodo, Aug 24–30 2026).

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
10. **Escalation** *(optional)* — notify if approved flag sits unreviewed too long

---

## TrueForge Integration

This project runs on [TrueForge](https://github.com/truefoundry/trueforge), TrueFoundry's open-source agent harness. The `agent.json` manifest at the project root defines:

- **MCP Tool Servers**: Two stdio-based MCP servers (`agent/mcp_imagery_server.py` for satellite imagery fetch, `agent/mcp_dashboard_server.py` for dashboard read/write)
- **Human Approval Gates**: `write_flag` and `retract_flag` tools are gated by `interrupt_config` — the agent cannot invoke them without explicit human sign-off
- **Daytona Sandbox**: NDVI/NDWI computation runs in an isolated sandbox with only `numpy` and `core/` available

### Running with TrueForge

```bash
# Install TrueForge
pip install trueforge

# Start the agent (reads agent.json automatically)
trueforge run --config agent.json
```

---

## Setup (standalone / development)

```bash
# Clone and create venv
git clone https://github.com/KrishnaRaghavendra05/Overwatch.git
cd Overwatch
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Fill in: MODEL_API_KEY (Gemini), IMAGERY_PROVIDER_URL, etc.

# Seed demo data & run agent CLI
python -m agent.main --scenario crop_damage

# Run the dashboard
uvicorn dashboard.app:app --reload

# Run tests
pytest
ruff check .
```

---

## Qodo Integration

This repository is configured with **Qodo Merge (PR-Agent)** and **Qodo Cover** via GitHub Actions:

- **`.pr_agent.toml`**: Custom rules enforcing `core/` architectural purity, satellite index scale boundaries (`[-1.0, 1.0]`), human-gated approval checks, and Pydantic boundary validation.
- **`.github/workflows/pr_agent.yml`**: Runs automated code reviews on pull requests and handles PR comment commands (`/review`, `/describe`, `/improve`, `/ask`, `/test`).
- **`.github/workflows/qodo_cover.yml`**: Automated test generation and coverage expansion.

```bash
# Available PR Comment Commands
/review       # Request automated Qodo code review
/describe     # Auto-generate PR summary and labels
/improve      # Request targeted code improvements
/ask <query>  # Ask questions about PR changes
/test         # Generate pytest unit tests for PR diff
```

---

## Demo

<!-- TODO: embed 3-minute demo video link before submission -->

---

## Judging criteria mapping

| Criterion | Where it shows |
|---|---|
| Potential impact | Agricultural-insurance framing: agent gates a real-money claim decision |
| Creativity | Geospatial/remote-sensing agents rare at this hackathon |
| Technical excellence | Deterministic index pipeline; write/verify/retract loop; 16+ automated tests |
| Use of sponsor tools | MCP tool call, Daytona sandbox, human-approval pause, subagent delegation, Qodo PR trail |
| Control & safety | Three real gates: Step 4.5 (ambiguity triage), Step 6 (file), Step 9 (retract) |
| Presentation | Before/after satellite imagery with Leaflet map + dashboard updating on approval |

---

## Qodo Code Review Evidence

All substantive features were developed through GitHub Pull Requests with Qodo code review enabled from commit #1. High-severity findings were addressed before merging.

<!-- Add links to merged PRs with Qodo review comments here:
- PR #1: Core math engine — https://github.com/.../pull/1
- PR #2: Verification subagents — https://github.com/.../pull/2
- PR #3: Dashboard & approval gates — https://github.com/.../pull/3
-->

---

## AI tool disclosure

This project used AI coding assistants during development, as permitted by hackathon rules:

- **Google Gemini** — used as the LLM model for executive report synthesis within the agent pipeline (`agent/llm_gemini.py`)
- **Claude (Anthropic)** — used as a pair-programming assistant for code generation, architecture design, and debugging throughout the build week
- **Qodo** — used for automated code review on all pull requests

All AI-generated code was reviewed, tested, and validated by human team members before merging. The mathematical core (`core/`) was independently verified against known index formulas and threshold values.
