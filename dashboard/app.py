import logging
import uuid
from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agent.llm_gemini import generate_executive_analysis
from agent.main import SCENARIOS
from agent.models.dashboard import ChangeFlag
from agent.services.cache import get_or_fetch
from agent.workflow.approval_gate import execute_approved_write
from agent.workflow.draft_report import draft_report, run_verification_suite
from agent.workflow.retraction import (
    execute_approved_retraction,
    propose_retraction,
)
from dashboard.read import list_flags, read_flag

logger = logging.getLogger(__name__)

app = FastAPI(title="Overwatch — Geospatial Verification Dashboard")
templates = Jinja2Templates(directory="dashboard/templates")

# In-memory store for active TrueForge interactive human-gate sessions
ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}


class AgentRunRequest(BaseModel):
    scenario_key: str | None = None
    custom_name: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    min_lat: float | None = None
    min_lon: float | None = None
    max_lat: float | None = None
    max_lon: float | None = None
    start_date: str | None = None
    end_date: str | None = None
    hazard_type: str | None = "crop_stress"  # "crop_stress", "flood", "wildfire"
    index_type: str | None = None


class GateDecisionRequest(BaseModel):
    session_id: str
    decision: str  # "APPROVE", "REJECT", "ACCEPT_AS_DAMAGE", "DISCARD"
    approver: str = "Human Assessor (Web Console)"


class RetractRequest(BaseModel):
    record_id: str
    approver: str = "Web Dashboard Operator"
    reason: str = "Human operator requested verified rollback via Dashboard UI"


# status page — shows all flag records and interactive satellite map
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    flags = list_flags()
    flags_json = [f.model_dump(mode="json") for f in flags]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "flags": flags,
            "flags_json": flags_json,
            "scenarios": SCENARIOS,
        },
    )


# json list of all flags
@app.get("/flags")
async def flags_list() -> list[dict[str, Any]]:
    flags = list_flags()
    return [f.model_dump(mode="json") for f in flags]


# json detail for single flag
@app.get("/flags/{record_id}")
async def flag_detail(record_id: str) -> dict[str, Any]:
    flag = read_flag(record_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag record not found")
    return flag.model_dump(mode="json")


# TrueForge API: Run agent workflow on preset or custom coordinates & dates
@app.post("/api/agent/run")
async def api_agent_run(req: AgentRunRequest) -> dict[str, Any]:
    from agent.models.imagery import BoundingBox, DateRange

    # 1. Resolve Scenario configuration (Preset vs Custom)
    if req.scenario_key and req.scenario_key in SCENARIOS:
        cfg = SCENARIOS[req.scenario_key]
        name = cfg["name"]
        area = cfg["area"]
        d_before = cfg["d_before"]
        d_after = cfg["d_after"]
        index_type = cfg["index_type"]
    else:
        # Check if coordinates match Iowa Cornfield preset
        if (
            req.min_lat is not None
            and abs(req.min_lat - 42.01) < 0.05
            and abs(req.min_lon - (-93.55)) < 0.05
        ):
            cfg = SCENARIOS["crop_damage"]
            name = cfg["name"]
            area = cfg["area"]
            d_before = cfg["d_before"]
            d_after = cfg["d_after"]
            index_type = cfg["index_type"]
        elif (
            req.min_lat is not None
            and abs(req.min_lat - 26.20) < 0.05
            and abs(req.min_lon - 92.50) < 0.05
        ):
            cfg = SCENARIOS["flood"]
            name = cfg["name"]
            area = cfg["area"]
            d_before = cfg["d_before"]
            d_after = cfg["d_after"]
            index_type = cfg["index_type"]
        elif (
            req.min_lat is not None
            and abs(req.min_lat - 36.70) < 0.05
            and abs(req.min_lon - (-119.80)) < 0.05
        ):
            cfg = SCENARIOS["ambiguous_haze"]
            name = cfg["name"]
            area = cfg["area"]
            d_before = cfg["d_before"]
            d_after = cfg["d_after"]
            index_type = cfg["index_type"]
        elif req.min_lat is not None and abs(req.min_lat - (-3.45)) < 0.05:
            cfg = SCENARIOS["cloud_false_positive"]
            name = cfg["name"]
            area = cfg["area"]
            d_before = cfg["d_before"]
            d_after = cfg["d_after"]
            index_type = cfg["index_type"]
        else:
            if None in (req.min_lat, req.min_lon, req.max_lat, req.max_lon):
                raise HTTPException(
                    status_code=400,
                    detail="Custom run requires min_lat, min_lon, max_lat, max_lon",
                )

            area = BoundingBox(
                min_lon=round(req.min_lon, 4),
                min_lat=round(req.min_lat, 4),
                max_lon=round(req.max_lon, 4),
                max_lat=round(req.max_lat, 4),
            )
            s_date = (
                date.fromisoformat(req.start_date)
                if req.start_date
                else date(2026, 6, 1)
            )
            e_date = (
                date.fromisoformat(req.end_date) if req.end_date else date(2026, 7, 15)
            )
            d_before = DateRange(
                start=s_date,
                end=date(s_date.year, s_date.month, min(28, s_date.day + 1)),
            )
            d_after = DateRange(
                start=e_date,
                end=date(e_date.year, e_date.month, min(28, e_date.day + 1)),
            )
            index_type = req.index_type or (
                "NDWI" if req.hazard_type == "flood" else "NDVI"
            )
            loc_desc = (
                " > ".join(filter(None, [req.country, req.state, req.city]))
                or "Custom Target Area"
            )
            name = (
                req.custom_name
                or f"{loc_desc} ({req.hazard_type.replace('_', ' ').title()})"
            )
            cfg = {
                "name": name,
                "area": area,
                "d_before": d_before,
                "d_after": d_after,
                "index_type": index_type,
            }

    session_id = f"tf_sess_{uuid.uuid4().hex[:8]}"

    # Step 2: Fetch Imagery (MCP Tool Call)
    before_resp = get_or_fetch(area, d_before)
    after_resp = get_or_fetch(area, d_after)

    # Step 3 & 4: Sandbox Math + 3 Subagents
    mean_delta, summary = run_verification_suite(
        before_resp, after_resp, d_after, index_type=index_type
    )

    # Step 5: Draft Insurance Dossier & AI assessment
    flag: ChangeFlag | None = None
    ai_briefing = ""
    gate_required = "NONE"

    if not summary.all_passed:
        gate_required = "DISCARDED_FALSE_ALARM"
    elif summary.is_ambiguous:
        gate_required = "AMBIGUITY_GATE"
        flag = draft_report(
            area,
            mean_delta,
            summary,
            before_resp,
            after_resp,
            index_type=index_type,
            hazard_name=name,
        )
        ai_briefing = generate_executive_analysis(
            name, mean_delta, index_type, flag.report_text
        )
        flag.report_text += (
            f"\n\n## 4. AI Actuarial Remote Sensing Review\n{ai_briefing}"
        )
    else:
        gate_required = "APPROVAL_GATE"
        flag = draft_report(
            area,
            mean_delta,
            summary,
            before_resp,
            after_resp,
            index_type=index_type,
            hazard_name=name,
        )
        ai_briefing = generate_executive_analysis(
            name, mean_delta, index_type, flag.report_text
        )
        flag.report_text += (
            f"\n\n## 4. AI Actuarial Remote Sensing Review\n{ai_briefing}"
        )

    # Construct step-by-step TrueForge Thinking & Trace Events
    subagent_lines = []
    for r in summary.results:
        st = (
            "PASS ✅"
            if r.passed and not r.is_ambiguous
            else ("AMBIGUOUS ⚠️" if r.is_ambiguous else "FAIL ❌")
        )
        subagent_lines.append(
            f"  • [{r.check_name.upper()}]: {st} — {r.details} ({r.confidence:.0%})"
        )

    formula_str = (
        "NDWI = (Green - NIR)/(Green + NIR)"
        if index_type == "NDWI"
        else "NDVI = (NIR - Red)/(NIR + Red)"
    )

    trace_events = [
        {
            "step": 1,
            "type": "thought",
            "title": "Goal Formulation & Scope Analysis",
            "text": (
                f"User requested claim assessment for '{name}'.\n"
                f"Dates: {d_before.start} -> {d_after.end}.\n"
                "Querying Sentinel-2 surface reflectance catalog via MCP..."
            ),
            "tag": "THOUGHT",
            "tag_class": "tag-purple",
        },
        {
            "step": 2,
            "type": "action",
            "title": "MCP Tool Call: mcp://overwatch-imagery/fetch_imagery",
            "text": (
                f"Target BBox: [{area.min_lat:.3f}, {area.min_lon:.3f}] to "
                f"[{area.max_lat:.3f}, {area.max_lon:.3f}].\n"
                "→ Ingested Sentinel-2 Bands: NIR, Red, Green, SCL Layer.\n"
                f"→ Baseline cloud: {before_resp.cloud_cover_pct_0_100:.1f}% | "
                f"Assessment cloud: {after_resp.cloud_cover_pct_0_100:.1f}%."
            ),
            "tag": "MCP TOOL",
            "tag_class": "tag-blue",
        },
        {
            "step": 3,
            "type": "sandbox",
            "title": "Daytona Sandbox Execution: Pure Math Delta",
            "text": (
                f"Daytona sandbox runtime invoked.\n"
                f"Formula: {formula_str}\n"
                f"→ Mean {index_type} Delta: {mean_delta:+.3f} (Scale -2 to +2)."
            ),
            "tag": "DAYTONA SANDBOX",
            "tag_class": "tag-blue",
        },
        {
            "step": 4,
            "type": "subagents",
            "title": "3 Concurrent Verification Subagents Disproof Audit",
            "text": (
                f"Raw signal ({mean_delta:+.3f}) detected. Dispatched 3 subagents:\n"
                + "\n".join(subagent_lines)
                + f"\n→ Verification Confidence: {summary.composite_confidence:.1%}"
            ),
            "tag": "SUBAGENTS",
            "tag_class": (
                "tag-green"
                if summary.all_passed and not summary.is_ambiguous
                else ("tag-yellow" if summary.is_ambiguous else "tag-red")
            ),
        },
        {
            "step": 5,
            "type": "thought",
            "title": "Claim Dossier Synthesis & Actuarial AI Review",
            "text": (
                f"Status: {summary.rationale}.\n"
                "Compiling Agricultural Insurance Claim Dossier.\n"
                "Synthesizing physical damage % and invoking Gemini AI."
            ),
            "tag": "AI ACTUARIAL",
            "tag_class": "tag-purple",
        },
    ]

    if gate_required == "DISCARDED_FALSE_ALARM":
        trace_events.append(
            {
                "step": 6,
                "type": "discard",
                "title": "Signal Disproved by Verification Subagents",
                "text": (
                    f"ALERT DISPROVED: {summary.rationale}.\n"
                    "Discarded as optical false alarm without filing a claim."
                ),
                "tag": "DISCARDED",
                "tag_class": "tag-red",
            }
        )
    elif gate_required == "AMBIGUITY_GATE":
        trace_events.append(
            {
                "step": 6,
                "type": "interrupt",
                "title": "TrueForge Ambiguity Triage Gate Triggered",
                "text": (
                    "INTERRUPT: Atmospheric haze or cirrus obstruction detected.\n"
                    "Pauses filing and routes to Human Ambiguity Triage."
                ),
                "tag": "AMBIGUITY GATE",
                "tag_class": "tag-yellow",
            }
        )
    else:
        trace_events.append(
            {
                "step": 6,
                "type": "interrupt",
                "title": "TrueForge Final Human Approval Gate: HITL Pause",
                "text": (
                    "⚠️ CONSEQUENTIAL ACTION: Legal/financial liability.\n"
                    "Harness requires explicit Human Actuarial sign-off.\n"
                    "Pausing workflow at Human Approval Gate..."
                ),
                "tag": "HITL PAUSE ACTIVE",
                "tag_class": "tag-yellow",
            }
        )

    # Store in active sessions for interactive human decision
    ACTIVE_SESSIONS[session_id] = {
        "cfg": cfg,
        "flag": flag,
        "summary": summary,
        "mean_delta": mean_delta,
        "gate_required": gate_required,
    }

    return {
        "session_id": session_id,
        "scenario": cfg["name"],
        "area": cfg["area"].model_dump(),
        "index_type": cfg["index_type"],
        "trace_events": trace_events,
        "step_2_mcp": {
            "tool": "mcp://overwatch-imagery/fetch_imagery",
            "baseline_date": str(before_resp.acquired.date()),
            "baseline_clouds": before_resp.cloud_cover_pct_0_100,
            "current_date": str(after_resp.acquired.date()),
            "current_clouds": after_resp.cloud_cover_pct_0_100,
        },
        "step_3_sandbox": {
            "provider": "Daytona",
            "formula": (
                "NDWI = (Green - NIR)/(Green + NIR)"
                if cfg["index_type"] == "NDWI"
                else "NDVI = (NIR - Red)/(NIR + Red)"
            ),
            "mean_delta": round(mean_delta, 3),
        },
        "step_4_subagents": [
            {
                "check_name": r.check_name,
                "passed": r.passed,
                "is_ambiguous": r.is_ambiguous,
                "details": r.details,
                "confidence": round(r.confidence, 2),
            }
            for r in summary.results
        ],
        "composite_confidence": round(summary.composite_confidence, 2),
        "gate_required": gate_required,
        "rationale": summary.rationale,
        "dossier_text": flag.report_text if flag else None,
        "ai_briefing": ai_briefing,
    }


# TrueForge API: Submit Human Approval Gate Decision
@app.post("/api/agent/decision")
async def api_agent_decision(req: GateDecisionRequest) -> dict[str, Any]:
    sess = ACTIVE_SESSIONS.get(req.session_id)
    if not sess:
        raise HTTPException(
            status_code=404, detail="Active TrueForge session expired or not found"
        )

    decision = req.decision.upper()
    flag: ChangeFlag | None = sess.get("flag")

    if decision == "REJECT" or decision == "DISCARD":
        del ACTIVE_SESSIONS[req.session_id]
        return {
            "status": "REJECTED_BY_HUMAN",
            "message": "Human assessor rejected claim filing. Action aborted.",
        }

    if decision in ("APPROVE", "ACCEPT_AS_DAMAGE"):
        if not flag:
            raise HTTPException(
                status_code=400, detail="No report available for approval"
            )
        # Execute consequential write via Approval Gate
        resp = execute_approved_write(flag, approver=req.approver)
        del ACTIVE_SESSIONS[req.session_id]
        return {
            "status": "VERIFIED_FILED",
            "record_id": resp.record_id,
            "written_at": resp.written_at.isoformat(),
            "area": resp.area.model_dump(),
        }

    raise HTTPException(status_code=400, detail=f"Unknown decision: {decision}")


# TrueForge API: Human-gated Retraction
@app.post("/api/agent/retract")
async def api_agent_retract(req: RetractRequest) -> dict[str, Any]:
    flag = read_flag(req.record_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Record not found")
    if flag.status == "RETRACTED":
        return {"status": "ALREADY_RETRACTED"}

    propose_retraction(req.record_id, reason=req.reason, interactive=False)
    resp = execute_approved_retraction(req.record_id, approver=req.approver)
    return {
        "status": "RETRACTED",
        "record_id": resp.record_id,
        "written_at": resp.written_at.isoformat(),
    }
