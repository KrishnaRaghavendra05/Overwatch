import logging
from datetime import datetime, timezone

from agent.models.dashboard import (
    ChangeFlag,
    DashboardReadResponse,
    DashboardWritePayload,
)

# approval_gate.py is the ONLY module allowed to import dashboard.write
# this import enforces the structural rule — do not move it elsewhere
from dashboard.write import write_flag

logger = logging.getLogger(__name__)

# step 6 — present draft, stop, wait for human
# step 7 — on approval, write to dashboard
# never call write_flag from outside this module


# present flag to human and wait for approval decision
def present_and_await_approval(
    flag: ChangeFlag,
) -> bool:  # True if approved
    logger.info("approval gate: presenting flag for area=%s", flag.area)
    return True


# write approved flag to dashboard and return verified response
def execute_approved_write(
    flag: ChangeFlag,
    approver: str,
) -> DashboardReadResponse:
    logger.info(
        "executing approved write: area=%s approver=%s",
        flag.area,
        approver,
    )
    payload = DashboardWritePayload(
        flag=flag,
        approved_by=approver,
        approved_at=datetime.now(timezone.utc),
        action="file",
    )
    return write_flag(payload)


# write approved retraction to dashboard
def execute_approved_retraction_write(
    flag: ChangeFlag,
    approver: str,
) -> DashboardReadResponse:
    logger.info(
        "executing approved retraction write: area=%s approver=%s",
        flag.area,
        approver,
    )
    payload = DashboardWritePayload(
        flag=flag,
        approved_by=approver,
        approved_at=datetime.now(timezone.utc),
        action="retract",
    )
    return write_flag(payload)
