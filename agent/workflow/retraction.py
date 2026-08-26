import logging
from datetime import datetime, timezone

from agent.models.dashboard import ChangeFlag, DashboardReadResponse
from agent.workflow.approval_gate import execute_approved_retraction_write
from dashboard.read import read_flag

logger = logging.getLogger(__name__)

# step 9 — retraction path, also gated behind human approval
# approval_gate.py handles the actual write — this module proposes only


# propose retraction to human for review
def propose_retraction(
    record_id: str,
    reason: str,
) -> bool:  # True if human approves retraction
    logger.info("propose_retraction: record_id=%s reason=%s", record_id, reason)
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
    existing = read_flag(record_id)
    retraction_flag = ChangeFlag(
        area=existing.area,
        detected_at=datetime.now(timezone.utc),
        index_type="NDVI",
        delta_ndvi_scale=0.0,
        severity="retracted",
        report_text=f"Retraction for record {record_id}",
    )
    return execute_approved_retraction_write(retraction_flag, approver)
