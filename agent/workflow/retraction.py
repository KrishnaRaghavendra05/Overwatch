import logging

from agent.models.dashboard import DashboardReadResponse

logger = logging.getLogger(__name__)

# step 9 — retraction path, also gated behind human approval
# approval_gate.py handles the actual write — this module proposes only


# propose retraction to human for review
def propose_retraction(
    record_id: str,
    reason: str,
) -> bool:  # True if human approves retraction
    logger.info("propose_retraction: record_id=%s reason=%s", record_id, reason)
    raise NotImplementedError


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
    raise NotImplementedError
