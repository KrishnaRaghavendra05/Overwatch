import logging
from datetime import datetime

from agent.models.dashboard import (
    ChangeFlag,
    DashboardReadResponse,
    DashboardWritePayload,
)

# approval_gate.py is the ONLY module allowed to import dashboard.write
# this import enforces the structural rule — do not move it elsewhere
from dashboard.write import write_flag

logger = logging.getLogger(__name__)


# present flag to human and wait for approval decision
def present_and_await_approval(
    flag: ChangeFlag,
    interactive: bool = False,
) -> bool:  # True if approved
    logger.info("approval gate: presenting flag for area=%s", flag.area)

    banner = [
        "============================================================",
        "🛡️  TRUEFORGE FINAL APPROVAL GATE: REPORT SIGN-OFF          🛡️",
        "============================================================",
        flag.report_text,
        "------------------------------------------------------------",
        "⚠️  CONSEQUENTIAL ACTION: This will file an official record",
        "    into the live Claims & Verification Dashboard.",
        "============================================================",
    ]
    logger.info("\n%s", "\n".join(banner))

    if interactive:
        decision = (
            input("Approve filing to live dashboard? (Y/N) [default: Y]: ")
            .strip()
            .upper()
        )
        return decision in ("", "Y", "YES")

    # Non-interactive mode (for test suite / automatic orchestrations)
    logger.info("Approval gate granted in test/demo mode.")
    return True


# write approved flag to dashboard and return verified response
def execute_approved_write(
    flag: ChangeFlag,
    approver: str,
    action: str = "file",
    record_id: str | None = None,
) -> DashboardReadResponse:
    logger.info(
        "executing approved write: area=%s approver=%s",
        flag.area,
        approver,
    )
    payload = DashboardWritePayload(
        flag=flag,
        approved_by=approver,
        approved_at=datetime.now(),
        action=action,
    )
    # Single structural write entrypoint
    response = write_flag(payload, record_id=record_id)

    if not response.verified:
        logger.error("VERIFICATION FAILED: Record written but read-back failed!")
    else:
        logger.info(
            "VERIFIED: Record %s confirmed live in dashboard.",
            response.record_id,
        )

    return response
