import logging

from agent.models.dashboard import DashboardReadResponse, DashboardWritePayload

logger = logging.getLogger(__name__)

# SINGLE write entrypoint for entire codebase
# nothing else may contain inline sql to this store
# only approval_gate.py imports this module


# write approved flag or retraction record, return verified read-back
def write_flag(
    payload: DashboardWritePayload,
) -> DashboardReadResponse:
    logger.info(
        "write_flag: action=%s area=%s approved_by=%s",
        payload.action,
        payload.flag.area,
        payload.approved_by,
    )
    raise NotImplementedError
