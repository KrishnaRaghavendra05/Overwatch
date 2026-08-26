import json
import logging
from datetime import datetime

from agent.models.dashboard import DashboardReadResponse
from agent.models.imagery import BoundingBox
from dashboard.db import get_connection

logger = logging.getLogger(__name__)

# step 8 — read back to verify write landed correctly


# fetch single flag record by id
def read_flag(
    record_id: str,
) -> DashboardReadResponse:
    logger.info("read_flag: record_id=%s", record_id)
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM flags WHERE record_id = ?",
            (record_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        msg = f"read_flag: record_id={record_id} not found"
        logger.error(msg)
        raise KeyError(msg)

    return _row_to_response(row)


# list all flag records
def list_flags() -> list[DashboardReadResponse]:
    logger.info("list_flags called")
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM flags ORDER BY written_at DESC",
        ).fetchall()
    finally:
        conn.close()

    return [_row_to_response(row) for row in rows]


# convert sqlite row to pydantic response
def _row_to_response(row: dict) -> DashboardReadResponse:
    area = BoundingBox(**json.loads(row["area_json"]))
    return DashboardReadResponse(
        record_id=row["record_id"],
        status=row["status"],
        written_at=datetime.fromisoformat(row["written_at"]),
        area=area,
        verified=True,
    )
