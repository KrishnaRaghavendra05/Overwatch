# Overwatch (TerraProof) — 3-Minute Video Demo Script

> **Goal**: Present the end-to-end TrueForge Agent Harness workflow to judges in 180 seconds.
> **Framing**: Agricultural Insurance Crop Loss & Flood Claim Assessment.

---

## ⏱️ Timeline & Talking Points

```
[0:00 - 0:25] 1. Problem & Real Stakes (Agricultural Insurance)
[0:25 - 0:55] 2. Trigger & MCP Satellite Ingestion
[0:55 - 1:30] 3. Daytona Sandboxed Math & 3 Parallel Subagents
[1:30 - 2:05] 4. Claim Dossier & Gemini Remote Sensing Assessment
[2:05 - 2:35] 5. 🛑 Human Approval Gate & Live Dashboard Write
[2:35 - 3:00] 6. Read-Back Verification & Retraction Safety Path
```

---

### [0:00 - 0:25] 1. Introduction & Agricultural Insurance Framing

- **Screen**: Overwatch Dashboard homepage (`http://localhost:8000`) with interactive Leaflet map and empty claims queue.
- **Narrator**:
  > *"Every season, agricultural insurers process thousands of drought, heat-stress, and flood claims. Eyeballing satellite imagery manually is slow and prone to false positives caused by passing clouds and sensor noise. Overwatch is an autonomous remote-sensing agent built on TrueForge that investigates real environmental changes, disproves false alarms with parallel subagents, and strictly gates financial payout decisions behind human approval."*

---

### [0:25 - 0:55] 2. Scenario Trigger & Real MCP Tool Call

- **Screen**: Click **"Run TrueForge Agent"** on the *Iowa Corn Canopy (Severe Crop Stress)* scenario.
- **Narrator**:
  > *"When an assessor or scheduled policy check queries a parcel, TrueForge initiates the investigation. First, the agent calls an external MCP tool (`mcp://overwatch-imagery/fetch_imagery`) to ingest multi-spectral Sentinel-2 Level-2A imagery from Microsoft Planetary Computer across two acquisition passes—capturing Near-Infrared, Red, Green, and the Scene Classification Layer (SCL)."*
- **Key Callout**: Point out the live trace event: `[Step 2] Ingested Sentinel-2 Bands: NIR, Red, Green, SCL Layer`.

---

### [0:55 - 1:30] 3. Daytona Sandbox Computation & 3 Verification Subagents

- **Screen**: Agent execution trace moving through Sandbox calculation and Subagents card.
- **Narrator**:
  > *"Rather than relying on hallucinated numbers, TrueForge spins up a Daytona container sandbox to compute deterministic index mathematics. It calculates an NDVI drop of -0.945 across 1,830 hectares.*
  >
  > *Before believing this signal, TrueForge dispatches three independent verification subagents in parallel to disprove it:*
  > 1. *The **Cloud/Shadow Subagent** checks the SCL mask: 0% shadow contamination (PASS).*
  > 2. *The **Threshold Subagent** checks if the delta exceeds the severe crop floor of -0.20 (PASS).*
  > 3. *The **Weather Cross-Check Subagent** confirms an anomalous heat crash during peak growing season (PASS).*
  >
  > *Because all three subagents agree with 93% composite confidence, the alert survives."*

---

### [1:30 - 2:05] 4. Actuarial Claim Dossier & Gemini AI Briefing

- **Screen**: Show the generated **Claim Dossier** and **AI Remote Sensing Assessment** markdown cards in the UI.
- **Narrator**:
  > *"The agent synthesizes a formal Agricultural Insurance Claim Dossier: quantifying 99.2% canopy biomass loss across 4,523 insured acres, with full multi-spectral provenance. Google Gemini provides an actuarial executive briefing ready for legal underwriters."*

---

### [2:05 - 2:35] 5. 🛑 The Human Approval Gate (Key Safety Moment)

- **Screen**: Show the pulsing yellow **"HITL PAUSE ACTIVE: Human Approval Required"** banner and the **[Approve Claim]** / **[Reject]** buttons.
- **Narrator**:
  > *"Crucially, the agent stops dead in its tracks. In TrueForge, consequential actions that carry real financial or legal liability cannot execute autonomously. `write_flag` is protected by `interrupt_config`.*
  >
  > *The human assessor reviews the imagery, verifies the subagent audit, and clicks **Approve Claim**."*

---

### [2:35 - 3:00] 6. Dashboard Write, Read-Back Verification & Retraction Path

- **Screen**: Click **[Approve Claim]**. Watch the live claims table update with `Status: FILED` and green `VERIFIED` badge.
- **Narrator**:
  > *"Instantly, the approved record is written into the live SQLite database. Step 8 immediately queries the database back to verify that the record landed with exact coordinates and timestamp.*
  >
  > *If subsequent cloud-free passes ever reveal a missed atmospheric shadow, Overwatch features a symmetrical **Retraction Gate**—allowing underwriters to propose a rollback that again requires human approval.*
  >
  > *Overwatch delivers real remote sensing tools, sandboxed math, subagent verification, and airtight human safety on TrueForge."*

---

## 🎯 Quick Demo Run Checklist

1. Start server:
   ```bash
   uvicorn dashboard.app:app --reload --port 8000
   ```
2. Open `http://localhost:8000` in browser.
3. Test 1: Run **Iowa Corn Canopy** (shows full pass -> Dossier -> Human Approval -> Filed).
4. Test 2: Run **Amazon Rainforest Sector 12** (shows Cloud Subagent failing -> instant rejection of false positive).
5. Show `pytest -v` passing (16/16 tests) and `scripts/run_qodo.py` passing Qodo architecture rules.
