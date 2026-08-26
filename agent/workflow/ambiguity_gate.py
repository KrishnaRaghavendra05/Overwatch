import logging
from enum import Enum

from agent.models.verification import VerificationSummary

logger = logging.getLogger(__name__)


# options available during human ambiguity triage
class TriageDecision(str, Enum):
    ACCEPT_AS_DAMAGE = "ACCEPT_AS_DAMAGE"
    FETCH_NEXT_DATE = "FETCH_NEXT_DATE"
    DISCARD_ARTIFACT = "DISCARD_ARTIFACT"


# step 4.5 — human triage when subagents detect ambiguity or split evidence
def handle_ambiguity_triage(
    summary: VerificationSummary,
    default_choice: TriageDecision = TriageDecision.ACCEPT_AS_DAMAGE,
    interactive: bool = False,
) -> TriageDecision:
    logger.warning("AMBIGUITY GATE TRIGGERED: %s", summary.rationale)

    triage_prompt = [
        "============================================================",
        "⚠️  TRUEFORGE AMBIGUITY TRIAGE GATE: HUMAN REVIEW REQUIRED  ⚠️",
        "============================================================",
        f"Rationale: {summary.rationale}",
        f"Composite Confidence: {summary.composite_confidence:.1%}",
        "Subagent Evidence Breakdown:",
    ]
    for r in summary.results:
        status = (
            "⚠️ AMBIGUOUS" if r.is_ambiguous else ("✅ PASS" if r.passed else "❌ FAIL")
        )
        triage_prompt.append(f"  [{status}] {r.check_name.upper()}: {r.details}")

    triage_prompt.extend(
        [
            "",
            "Available Actions:",
            "  1. [ACCEPT_AS_DAMAGE] Disregard haze and proceed to draft report",
            "  2. [FETCH_NEXT_DATE] Request subsequent cloud-free imagery tile",
            "  3. [DISCARD_ARTIFACT] Discard alert as atmospheric artifact",
            "============================================================",
        ]
    )

    logger.info("\n%s", "\n".join(triage_prompt))

    if interactive:
        choice = input("Enter choice (1, 2, or 3) [default: 1]: ").strip()
        if choice == "2":
            return TriageDecision.FETCH_NEXT_DATE
        if choice == "3":
            return TriageDecision.DISCARD_ARTIFACT
        return TriageDecision.ACCEPT_AS_DAMAGE

    logger.info("Non-interactive triage resolving with: %s", default_choice)
    return default_choice
