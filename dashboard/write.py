import hashlib
import json
import logging
from datetime import datetime

from agent.models.dashboard import DashboardReadResponse, DashboardWritePayload
from dashboard.db import get_connection, init_db
from dashboard.read import read_flag

logger = logging.getLogger(__name__)


# derive deterministic record ID for area + time
def _make_record_id(payload: DashboardWritePayload) -> str:
    area = payload.flag.area
    ts = payload.approved_at.isoformat()
    raw = (
        f"{area.min_lon}_{area.min_lat}_{area.max_lon}_"
        f"{area.max_lat}_{payload.flag.index_type}_{ts}"
    )
    return "flag_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


# write approved flag or retraction record, return verified read-back
def write_flag(
    payload: DashboardWritePayload,
    record_id: str | None = None,
) -> DashboardReadResponse:
    init_db()
    if record_id is None:
        record_id = _make_record_id(payload)
    written_at = datetime.now()
    status = "RETRACTED" if payload.action == "retract" else "FILED"

    logger.info(
        "write_flag: record_id=%s action=%s status=%s approver=%s",
        record_id,
        payload.action,
        status,
        payload.approved_by,
    )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO flags (
                record_id, area_json, index_type, delta_ndvi_scale,
                severity, report_text, status, approved_by,
                approved_at, action, written_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                status = excluded.status,
                action = excluded.action,
                approved_by = excluded.approved_by,
                approved_at = excluded.approved_at,
                written_at = excluded.written_at
            """,
            (
                record_id,
                json.dumps(payload.flag.area.model_dump()),
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

    # Step 8 Verification: Read back immediately to verify it landed correctly
    verification_read = read_flag(record_id)
    if not verification_read:
        raise RuntimeError(f"Database write verification failed for {record_id}")

    return verification_read
