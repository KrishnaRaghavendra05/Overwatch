import logging

from agent.models.dashboard import ChangeFlag, DashboardReadResponse

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
    raise NotImplementedError


# write approved flag to dashboard and return verified response
def execute_approved_write(
    flag: ChangeFlag,
    approver: str,
) -> DashboardReadResponse:
    logger.info("executing approved write: area=%s approver=%s", flag.area, approver)
    _ = write_flag
    raise NotImplementedError
