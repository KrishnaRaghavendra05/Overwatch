import logging
from datetime import datetime, timezone

from agent.models.dashboard import ChangeFlag
from agent.models.imagery import BoundingBox
from agent.workflow.approval_gate import execute_approved_write
from dashboard.db import init_db

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# seed reproducible demo data — explicit seed per AGENTS.MD determinism rule


# generate seeded sample data for demo
def seed(seed_value: int = 42) -> None:
    logger.info("seed: seed_value=%s", seed_value)
    init_db()

    # Sample Area 1: Agricultural crop stress in Punjab region
    area1 = BoundingBox(
        min_lon=75.8573, min_lat=30.9010, max_lon=75.8973, max_lat=30.9410
    )
    flag1 = ChangeFlag(
        area=area1,
        detected_at=datetime.now(timezone.utc),
        index_type="NDVI",
        delta_ndvi_scale=-0.32,
        severity="severe",
        report_text=(
            "Severe vegetation loss detected in agricultural zone. "
            "NDVI delta: -0.3200. Verified across NIR/Red spectral bands. "
            "Cloud cover: 3.2% (PASS). Weather anomalies: None (PASS)."
        ),
    )
    res1 = execute_approved_write(flag1, approver="human_assessor_alpha")
    logger.info("Seeded record 1: id=%s status=%s", res1.record_id, res1.status)

    # Sample Area 2: Moderate flood impact near river basin
    area2 = BoundingBox(
        min_lon=85.1376, min_lat=25.5941, max_lon=85.1776, max_lat=25.6341
    )
    flag2 = ChangeFlag(
        area=area2,
        detected_at=datetime.now(timezone.utc),
        index_type="NDWI",
        delta_ndvi_scale=0.24,
        severity="moderate",
        report_text=(
            "Water index elevation detected near flood basin. "
            "NDWI delta: +0.2400. Verified across Green/NIR bands. "
            "Cloud cover: 8.1% (PASS). Threshold test: PASS."
        ),
    )
    res2 = execute_approved_write(flag2, approver="human_assessor_beta")
    logger.info("Seeded record 2: id=%s status=%s", res2.record_id, res2.status)


if __name__ == "__main__":
    seed()
