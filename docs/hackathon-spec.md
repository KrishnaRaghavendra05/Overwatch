# Geospatial Change Verification Agent
### TrueForge / Agent Harness Hackathon — Problem Statement & Build Spec

---

## 1. Context: what this document is for

This is the full spec for a project being built for **The Agent Harness Hackathon** (WeMakeDevs × TrueFoundry, Aug 24–30 2026). It's written so another agent or developer picking this up cold has everything needed to start building — no prior conversation required.

**About the hackathon itself:**
- Runs on **TrueForge**, TrueFoundry's open-source agent harness (github.com/truefoundry/trueforge). TrueForge is the *runtime layer* that turns a plain LLM into an agent that can reach tools, run generated code safely, and pause for human approval before irreversible actions. Model, MCP tool servers, and the sandbox are all bring-your-own — TrueForge orchestrates them.
- **Non-negotiable requirement:** a judge must be able to see TrueForge (a) reaching a real tool, (b) running code in a sandbox, and (c) stopping to ask a human before an irreversible action. If the project would work just as well as a plain chatbot, it doesn't qualify.
- **Judged on 6 equally-weighted criteria:** Potential impact / Creativity and originality / Technical excellence / Use of sponsor tools (TrueForge centrality + Qodo PR review trail) / Control and safety / Presentation.
- **Deliverables:** public GitHub repo with a README a stranger can run, Qodo installed from commit #1 with a real PR history, and a ~3-minute demo video showing the agent working — submitted by Aug 30, 8PM London time.
- **Best practice the org explicitly states:** pick ONE narrow job the agent can finish end-to-end. A small, fully-working thing beats a bigger half-finished platform.

---

## 2. The problem statement, in one paragraph

Build an agent that monitors a specific geographic area for meaningful land-cover change — crop stress, flooding, or deforestation — by comparing satellite imagery across two dates. Before treating any detected change as real, the agent runs it through a set of verification checks designed to rule out common false positives (cloud cover, seasonal variation, sensor noise). Only a change that survives verification gets escalated into a draft report. The agent never files that report on its own — a human must approve it first. After approval, the agent writes the flag into a live tracking system and confirms the write succeeded. If later evidence contradicts an earlier approved flag, the agent can propose retracting it — again pending human approval.

---

## 3. Who this is for (ICP)

**Primary:** agricultural insurers / crop-damage assessors who currently rely on manual field inspection or a human analyst eyeballing imagery to process claims. This agent's shape (detect → verify → draft claim-worthy report → human sign-off) maps directly onto their real workflow, and "file an official damage assessment" is a genuinely consequential, real-money action — not an invented stake.

**Secondary:** environmental compliance / forestry monitoring bodies (government forest departments, conservation NGOs, supply-chain deforestation compliance teams) doing periodic area monitoring where a false alert has real regulatory/reputational cost.

**Tertiary:** disaster-response coordination teams doing flood-extent monitoring — lower monetization but the most visually dramatic demo material.

For the hackathon demo, **lead with the agricultural-insurance framing** — it gives the clearest "here's a real dollar decision this agent gates" story in the first 15 seconds, which is what a judge unfamiliar with remote sensing needs to get oriented fast.

---

## 4. Full agent workflow

**Step 1 — Trigger.** A user asks a plain-English question ("has this area near [place] shown deforestation/flooding/crop stress in the last N days?") or a scheduled check runs automatically.

**Step 2 — Fetch imagery (real tool reach).** The agent pulls two dates of optical satellite imagery for the target area from a public imagery source. This is the harness's MCP/tool-call layer in action — not data the user supplied, data the agent goes and gets.

**Step 3 — Compute the raw signal (sandboxed code).** The agent writes and runs code — inside TrueForge's sandbox, not on the host machine — to compute a change index between the two images (e.g. NDVI for vegetation/crop stress, NDWI for flood/water extent). Output: a raw "this area changed by X" signal.

**Step 4 — Verify before believing it (subagents, run in parallel).** Three checks try to disprove the raw signal rather than confirm it:
  - **Cloud/shadow check** — was cloud or cloud-shadow covering that pixel region in either image? If yes, the reading is unreliable and gets discarded.
  - **Weather cross-check** — was there recent heavy rainfall or a known seasonal pattern that would explain the change naturally, without anything abnormal happening?
  - **Threshold check** — does the raw change number actually cross a meaningful, pre-defined severity threshold, or is it within normal noise?

  Each check runs as its own subagent, concurrently — this is the harness's subagent-delegation feature being used for a real reason (parallel independent verification), not decoration.

**Step 5 — Draft the report.** Only if the change survives all three checks does the agent draft a report: what changed, where, how confident it is, and what it recommends (e.g. "flag for claims review" / "flag for compliance audit").

**Step 6 — Human approval gate (the core safety mechanism).** The agent presents the draft and stops. It does **not** file, publish, or act on it. A human must explicitly approve before anything happens next. This is the hackathon's central required capability — the demo's most important moment.

**Step 7 — Act on approval (real system write, not a static document).** Once approved, the agent writes the flag into a live tracking system — a small dashboard/database built for this project (e.g. a claims-queue table or a monitoring map) — so approval visibly changes the state of a real system, not just produces a downloadable file.

**Step 8 — Verify the action landed.** Immediately after writing, the agent queries the system back to confirm the record was created correctly (status, timestamp, area) — proving its own action worked, the same way a deploy agent would check that an error rate actually recovered after a rollback.

**Step 9 — Rollback path: retraction on new evidence.** If a later, cleaner image contradicts a previously-approved flag (e.g. it turns out to have been a cloud shadow the checks missed), the agent can propose retracting or correcting that record. This retraction is itself gated behind a fresh human approval — a genuine undo path, not a cosmetic one.

**Step 10 — (Optional, if time allows) Escalation.** If an approved flag sits unreviewed past some time window, the agent can escalate — notify a second channel, raise priority — demonstrating the harness handling ongoing state, not just one request/response cycle.

---

## 5. Mapping to TrueForge's 8 harness features

| Feature | Where it's used |
|---|---|
| MCP tool connections | Step 2, fetching imagery (custom MCP server wrapping a public imagery API, e.g. Microsoft Planetary Computer's STAC catalog) |
| Sandboxed code execution | Step 3 (index computation) and Step 4 (verification checks) — via Daytona, the sandbox provider TrueForge uses today |
| Human-approval pause | Step 6 (primary gate) and Step 9 (retraction gate) |
| Subagent delegation | Step 4 — three parallel verification checks |
| Reconnect-proof sessions | Free by default from the harness; matters if a check takes a while or the demo needs to survive a refresh |
| Model-agnostic | Not a design choice to make — just don't hardcode assumptions about a specific provider |
| Skills | Optional: package "compute NDVI/NDWI" and "check cloud mask" as reusable SKILL.md instruction packs the agent loads on demand — nice bonus polish, not required for a working demo |
| Scaling (SQLite→Postgres/Redis) | Not relevant at hackathon scale — local/standalone TrueForge mode is the right choice |

---

## 6. Technical scope — what to actually build

**In scope (build this):**
- One script/tool that fetches two dated images for a defined area from a public source
- One script that computes NDVI or NDWI difference between them (plain numpy-level math, not a trained ML model)
- Three small verification checks (cloud mask, weather cross-check, threshold test)
- A minimal dashboard/database (even a simple table + web page) that the agent writes to on approval and reads back to verify
- The approval-gate UI/flow showing pending → approved/rejected → written → verified
- The retraction flow (Step 9)
- A public GitHub repo with README, Qodo installed from commit #1, PRs opened throughout the week

**Explicitly out of scope for the hackathon week (would blow the timeline):**
- SAR imagery processing (calibration, speckle filtering, geocoding) — use optical imagery only
- Training a custom ML/CV model — use deterministic index math (NDVI/NDWI), not a trained classifier
- A general-purpose remote-sensing platform covering many change types — pick ONE (recommend crop stress or flood, whichever has cleaner sample data available)
- Full production infrastructure (Postgres/Redis/multi-replica) — local TrueForge mode is correct here
- Escalation (Step 10) — nice-to-have only if the core loop (Steps 1–9) is solid with time to spare

---

## 7. Why this design satisfies the judging criteria

- **Impact** — real decision (insurance claim / compliance flag), not a toy demo of a picture.
- **Creativity** — geospatial/remote-sensing agents are rare at this hackathon; most entrants will land in DevOps/SRE or generic chatbot-adjacent categories.
- **Technical excellence** — fully deterministic, testable pipeline (no ML training risk); the harder work is verification-check design and the write/verify/retract loop, all realistically completable in a week.
- **Use of sponsor tools** — hits 5+ of the 8 TrueForge features genuinely, not superficially; Qodo PR trail is independent of the idea and just requires discipline from commit #1.
- **Control & safety** — two real gates (initial approval + retraction approval), both with genuine real-world stakes, not decorative pauses.
- **Presentation** — before/after satellite imagery with a highlighted change region, plus a dashboard visibly updating on approval, is immediately legible to any judge in a 3-minute video regardless of their domain background.

---

## 8. Suggested build order (within the 7-day window)

1. Get TrueForge running locally, model connected, Daytona sandbox connected, a basic MCP tool for imagery fetch working end-to-end on sample data.
2. Get the index computation (Step 3) running correctly in the sandbox against known before/after image pairs.
3. Build the three verification subagents (Step 4) — start with the threshold check (simplest), then cloud mask, then weather cross-check.
4. Build the approval-gate UI and the write/verify loop (Steps 6–8) against the mock dashboard.
5. Build the retraction path (Step 9).
6. Polish UI, finalize README, ensure Qodo PR history is clean, record the 3-minute demo — lead the demo with the agricultural-insurance framing from Section 3.