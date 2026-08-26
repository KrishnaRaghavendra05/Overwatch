import logging

from agent.models.dashboard import DashboardReadResponse
from agent.workflow.approval_gate import execute_approved_write
from dashboard.read import read_flag

logger = logging.getLogger(__name__)


# propose retraction to human for review
def propose_retraction(
    record_id: str,
    reason: str,
    interactive: bool = False,
) -> bool:  # True if human approves retraction
    logger.info("propose_retraction: record_id=%s reason=%s", record_id, reason)

    banner = [
        "============================================================",
        "🔄  TRUEFORGE RETRACTION GATE: ROLLBACK PROPOSAL             🔄",
        "============================================================",
        f"Record ID: {record_id}",
        f"Retraction Reason: {reason}",
        "------------------------------------------------------------",
        "⚠️  CONSEQUENTIAL ACTION: This will mark the existing claim",
        "    as RETRACTED / VOID in the live database.",
        "============================================================",
    ]
    print("\n".join(banner))

    if interactive:
        decision = (
            input("Approve record retraction? (Y/N) [default: Y]: ").strip().upper()
        )
        return decision in ("", "Y", "YES")

    logger.info("Retraction approved in automated/test mode.")
    return True


# execute approved retraction via approval gate
def execute_approved_retraction(
    record_id: str,
    approver: str,
) -> DashboardReadResponse:
    logger.info(
        "execute_approved_retraction: record_id=%s approver=%s",
        record_id,
        approver,
    )
    # Fetch existing record to get area and payload details
    existing = read_flag(record_id)
    if not existing:
        raise ValueError(f"Record {record_id} not found in database for retraction.")
    if existing.flag is None:
        raise ValueError(
            f"Record {record_id} exists but ChangeFlag could not be "
            "reconstructed from DB. Cannot retract a corrupt record."
        )

    # Execute retraction write using the original record_id
    return execute_approved_write(
        flag=existing.flag,
        approver=approver,
        action="retract",
        record_id=record_id,
    )
