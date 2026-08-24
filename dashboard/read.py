import logging

from agent.models.dashboard import DashboardReadResponse

logger = logging.getLogger(__name__)

# step 8 — read back to verify write landed correctly


# fetch single flag record by id
def read_flag(
    record_id: str,
) -> DashboardReadResponse:
    logger.info("read_flag: record_id=%s", record_id)
    raise NotImplementedError


# list all flag records
def list_flags() -> list[DashboardReadResponse]:
    logger.info("list_flags called")
    raise NotImplementedError
