import json
import logging
import uuid
from datetime import datetime, timezone

from agent.models.dashboard import DashboardReadResponse, DashboardWritePayload
from agent.models.imagery import BoundingBox
from dashboard.db import get_connection

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

    record_id = str(uuid.uuid4())
    written_at = datetime.now(timezone.utc)
    area_json = payload.flag.area.model_dump_json()

    # status maps from action: "file" -> "filed", "retract" -> "retracted"
    status = "filed" if payload.action == "file" else "retracted"

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO flags
                (record_id, area_json, index_type, delta_ndvi_scale, severity,
                 report_text, status, approved_by, approved_at, action, written_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                area_json,
                payload.flag.index_type,
                payload.flag.delta_ndvi_scale,
                payload.flag.severity,
                payload.flag.report_text,
                status,
                payload.approved_by,
                payload.approved_at.isoformat(),
                payload.action,
                written_at.isoformat(),
            ),
        )
        conn.commit()

        # read back to verify write landed
        row = conn.execute(
            "SELECT * FROM flags WHERE record_id = ?",
            (record_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        msg = f"write verification failed: record_id={record_id} not found after insert"
        logger.error(msg)
        raise RuntimeError(msg)

    verified_area = json.loads(row["area_json"])
    logger.info("write_flag verified: record_id=%s status=%s", record_id, status)

    return DashboardReadResponse(
        record_id=record_id,
        status=row["status"],
        written_at=datetime.fromisoformat(row["written_at"]),
        area=BoundingBox(**verified_area),
        verified=True,
    )
