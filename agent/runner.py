"""Scenario runner — clean API for running Overwatch workflows.

Imported by dashboard/app.py and agent/main.py CLI.
Does NOT configure logging or call seed() — callers do that.
"""

import logging

from agent.llm_gemini import generate_executive_analysis
from agent.models.imagery import BoundingBox, DateRange
from agent.services.cache import get_or_fetch
from agent.workflow.ambiguity_gate import (
    TriageDecision,
    handle_ambiguity_triage,
)
from agent.workflow.approval_gate import (
    execute_approved_write,
    present_and_await_approval,
)
from agent.workflow.draft_report import (
    draft_report,
    run_verification_suite,
)

logger = logging.getLogger(__name__)


# run a single scenario end-to-end
def run_scenario(
    name: str,
    area: BoundingBox,
    d_before: DateRange,
    d_after: DateRange,
    index_type: str = "NDVI",
    interactive: bool = True,
    approver: str = "Kaamil Hifzaan",
) -> None:
    logger.info("=" * 65)
    logger.info("RUNNING OVERWATCH WORKFLOW: %s", name)
    logger.info("=" * 65)

    # Step 2: Fetch Imagery (MCP Tool Call)
    logger.info("[Step 2] Fetching optical bands via MCP tool call...")
    before_resp = get_or_fetch(area, d_before)
    after_resp = get_or_fetch(area, d_after)
    logger.info(
        "Baseline: %s | Clouds: %.1f%%",
        before_resp.acquired.date(),
        before_resp.cloud_cover_pct_0_100,
    )
    logger.info(
        "Current:  %s | Clouds: %.1f%%",
        after_resp.acquired.date(),
        after_resp.cloud_cover_pct_0_100,
    )

    # Step 3 & 4: Compute Index Delta & Run Subagents
    logger.info("[Step 3 & 4] Sandboxed Math + 3 Parallel Verification Subagents...")
    mean_delta, summary = run_verification_suite(
        before_resp, after_resp, d_after, index_type=index_type
    )
    logger.info("Raw %s Mean Delta: %+.3f", index_type, mean_delta)
    for res in summary.results:
        icon = (
            "PASS"
            if res.passed and not res.is_ambiguous
            else ("AMBIGUOUS" if res.is_ambiguous else "FAIL")
        )
        logger.info(
            "Subagent [%s]: %s — %s (Conf: %.0f%%)",
            res.check_name.upper(),
            icon,
            res.details,
            res.confidence * 100,
        )

    # Check if rejected
    if not summary.all_passed:
        logger.warning("ALERT DISPROVED: %s", summary.rationale)
        logger.info("Status: Discarded as false positive. No claim filed.")
        return

    # Step 4.5: Ambiguity Triage Gate
    if summary.is_ambiguous:
        logger.info("[Step 4.5] Ambiguity detected in subagent evidence.")
        decision = handle_ambiguity_triage(
            summary,
            default_choice=TriageDecision.ACCEPT_AS_DAMAGE,
            interactive=interactive,
        )
        if decision == TriageDecision.DISCARD_ARTIFACT:
            logger.info("Action: Discarded per human triage.")
            return
        if decision == TriageDecision.FETCH_NEXT_DATE:
            logger.info("Action: Requesting next cloud-free imagery pass.")
            return

    # Step 5: Draft Report & LLM Enrichment
    logger.info("[Step 5] Drafting Claim Dossier & Gemini Assessment...")
    flag = draft_report(
        area,
        mean_delta,
        summary,
        before_resp,
        after_resp,
        index_type=index_type,
    )

    ai_analysis = generate_executive_analysis(
        area_name=name,
        delta_val=mean_delta,
        index_type=index_type,
        evidence_text=flag.report_text,
    )
    flag.report_text += f"\n\n## AI Remote Sensing Assessment\n{ai_analysis}"

    # Step 6: Final Human Approval Gate
    logger.info("[Step 6] Halting for TrueForge Human Approval Gate...")
    approved = present_and_await_approval(flag, interactive=interactive)
    if not approved:
        logger.warning("Approval REJECTED by human. Action cancelled.")
        return

    # Step 7 & 8: Write to Dashboard & Verify Read-back
    logger.info("[Step 7 & 8] Writing approved flag & verifying read-back...")
    read_resp = execute_approved_write(flag, approver=approver)
    logger.info(
        "VERIFIED: Record %s filed. Timestamp: %s | Status: %s",
        read_resp.record_id,
        read_resp.written_at,
        read_resp.status,
    )
