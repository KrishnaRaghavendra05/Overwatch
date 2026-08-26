# TrueForge Hackathon & Overwatch Reference Guide

> **MANDATORY**: Review this file before generating code, planning architectures, or responding to hackathon build tasks.

---

## 1. Hackathon Overview & Constraints

- **Hackathon:** The Agent Harness Hackathon (WeMakeDevs × TrueFoundry × Qodo)
- **Dates:** August 24–30, 2026 (Closes Aug 30, 8:00 PM London time)
- **Teams:** Solo or up to 4 members
- **Core Technology Requirement:** Must run on **TrueForge** (`github.com/truefoundry/trueforge`). The harness must do real work, not act as a thin LLM wrapper.
- **The 3 Non-Negotiable Harness Pillars:**
  1. **Reach real tools via MCP** (Model Context Protocol).
  2. **Execute generated code in a sandbox** (Daytona sandbox execution).
  3. **Human Approval Gate** before any consequential / irreversible action (filing or retracting a claim/report).
- **Mandatory Qodo PR Workflow:**
  - Every substantive commit/feature MUST go through a GitHub Pull Request reviewed by Qodo.
  - Fix high-severity findings or document reasons for dismissal in PR threads.
  - README must include `## Qodo Code Review Evidence` with links to merged PRs.
- **AI Tool Disclosure:** Required in README/writeup. Be completely truthful about AI assistance.

---

## 2. Overwatch Project Architecture & Boundaries

```
                        +-----------------------------------------------+
                        |              TrueForge Agent                 |
                        |  1. Trigger (Plain text / Scheduled check)   |
                        |  2. Fetch Satellite Imagery (MCP Tool Call)  |
                        |  3. Compute NDVI/NDWI Delta (Daytona Sandbox)|
                        |  4. Run 3 Parallel Verification Subagents:   |
                        |     - Cloud/Shadow Check                     |
                        |     - Weather Cross-Check                    |
                        |     - Threshold Check                        |
                        |  4.5 [AMBIGUITY GATE] Human Triage if split  |
                        |  5. Draft Assessment Report                  |
                        |  6. [PAUSE] FINAL HUMAN APPROVAL GATE        |
                        |  7. Write Flag to Dashboard System           |
                        |  8. Read-back & Verify Write Confirmation    |
                        |  9. Retraction Gate (if later disproven)     |
                        +-----------------------------------------------+
                                     |             |
           (Math & Masking)          |             | (Write / Read)
                                     v             v
                    +--------------------+    +--------------------+
                    |      `core/`       |    |   `dashboard/`     |
                    | Pure Python/NumPy  |    | FastAPI + SQLite   |
                    | Zero Harness deps  |    | Live Claims Queue  |
                    | Enforced by Purity |    | Single Write Entry |
                    +--------------------+    +--------------------+
```

### Architectural Invariants:
1. **`core/` Purity:** NEVER import TrueForge, MCP, or `agent/` in `core/`. Math must be 100% deterministic and unit-tested in isolation (`test_purity.py`).
2. **Units & Scales:**
   - Reflectance scale: Standard Sentinel-2 is 0–10,000 (Surface Reflectance) or 0.0–1.0. Always confirm and document.
   - NDVI/NDWI: Range is strictly `-1.0` to `+1.0`. Delta range is `-2.0` to `+2.0`.
   - Cloud mask / SCL: Sentinel-2 Scene Classification Layer (SCL) values 0–11. Unreliable fraction: `0.0` to `1.0`.
3. **Single Write Path:** Only `dashboard/write.py` writes to the SQLite database. No inline SQL across the agent.
4. **Approval Strictness:** The agent CANNOT call `dashboard/write.py` directly without passing through the TrueForge human approval pause.

---

## 3. Work Breakdown Structure (3 Tracks)

| Track | Teammate | Focus Area | Key Files & Responsibilities |
|---|---|---|---|
| **Track 1** | **Kaamil (Lead / Core & Data)** | Math Engine, Imagery MCP, Caching, Test Goldens | `core/index_math.py`, `core/cloud_mask.py`, `core/thresholds.py`, `core/tests/`, `agent/models/imagery.py`, `agent/services/cache.py`, `agent/tools/fetch_imagery.py`, `scripts/seed_sample_data.py` |
| **Track 2** | **Teammate 2 (Harness & Subagents)** | Verification Subagents, Workflow State Machine, TrueForge HITL Gates | `agent/subagents/cloud_check.py`, `agent/subagents/weather_check.py`, `agent/subagents/threshold_check.py`, `agent/workflow/draft_report.py`, `agent/workflow/approval_gate.py`, `agent/workflow/retraction.py`, `agent.json` |
| **Track 3** | **Teammate 3 (Dashboard & Presentation)** | FastAPI Live Dashboard, Write/Verify Client, Leaflet UI, Qodo Evidence & Demo | `dashboard/db.py`, `dashboard/write.py`, `dashboard/read.py`, `dashboard/app.py`, `dashboard/templates/index.html`, `agent/models/dashboard.py`, `README.md` (Qodo section), Demo video |

---

## 4. Git & PR Quality Rules

- No robot attribution or tool trailers in commits (`No Co-Authored-By: Claude/GPT`).
- Keep commit messages punchy and descriptive.
- PRs must be opened against `main` for each module and reviewed with Qodo.
- High-severity Qodo suggestions must be addressed before merging.
