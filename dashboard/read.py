import json
import logging
from datetime import datetime

from agent.models.dashboard import DashboardReadResponse
from agent.models.imagery import BoundingBox
from dashboard.db import get_connection, init_db

logger = logging.getLogger(__name__)


# fetch single flag record by id
def read_flag(
    record_id: str,
) -> DashboardReadResponse | None:
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flags WHERE record_id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return None

        area_dict = json.loads(row["area_json"])
        area = BoundingBox.model_validate(area_dict)
        flag = None
        try:
            from agent.models.dashboard import ChangeFlag

            flag = ChangeFlag(
                area=area,
                detected_at=datetime.fromisoformat(row["approved_at"]),
                index_type=row["index_type"],
                delta_ndvi_scale=row["delta_ndvi_scale"],
                severity=row["severity"],
                report_text=row["report_text"],
            )
        except Exception:
            logger.exception(
                "Failed to reconstruct ChangeFlag for %s",
                record_id,
            )

        return DashboardReadResponse(
            record_id=row["record_id"],
            status=row["status"],
            written_at=datetime.fromisoformat(row["written_at"]),
            area=area,
            flag=flag,
            verified=True,
        )


# list all flag records
def list_flags() -> list[DashboardReadResponse]:
    init_db()
    results = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flags ORDER BY written_at DESC")
        for row in cursor.fetchall():
            area_dict = json.loads(row["area_json"])
            area = BoundingBox.model_validate(area_dict)
            flag = None
            try:
                from agent.models.dashboard import ChangeFlag

                flag = ChangeFlag(
                    area=area,
                    detected_at=datetime.fromisoformat(row["approved_at"]),
                    index_type=row["index_type"],
                    delta_ndvi_scale=row["delta_ndvi_scale"],
                    severity=row["severity"],
                    report_text=row["report_text"],
                )
            except Exception:
                logger.exception(
                    "Failed to reconstruct ChangeFlag for %s",
                    row["record_id"],
                )
            results.append(
                DashboardReadResponse(
                    record_id=row["record_id"],
                    status=row["status"],
                    written_at=datetime.fromisoformat(row["written_at"]),
                    area=area,
                    flag=flag,
                    verified=True,
                )
            )
    return results
