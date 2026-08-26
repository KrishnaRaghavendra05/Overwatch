import logging
from datetime import datetime, timezone

from agent.models.dashboard import ChangeFlag
from agent.models.imagery import BoundingBox
from core.thresholds import (
    NDVI_DELTA_MODERATE_NDVI_SCALE,
    NDVI_DELTA_SEVERE_NDVI_SCALE,
)

logger = logging.getLogger(__name__)

# step 5 — draft report only if all three verification checks passed


# build change flag report from verified signal
def draft_report(
    area: BoundingBox,
    delta_ndvi_scale: float,  # ndvi_delta, native -2..2 scale
    checks_passed: bool,
) -> ChangeFlag:
    logger.info(
        "draft_report: area=%s delta_ndvi_scale=%s checks_passed=%s",
        area,
        delta_ndvi_scale,
        checks_passed,
    )
    if not checks_passed:
        raise ValueError("Cannot draft report: verification checks failed")

    if delta_ndvi_scale <= NDVI_DELTA_SEVERE_NDVI_SCALE:
        severity = "severe"
    elif delta_ndvi_scale <= NDVI_DELTA_MODERATE_NDVI_SCALE:
        severity = "moderate"
    else:
        severity = "low"

    area_str = f"[{area.min_lon}, {area.min_lat}, {area.max_lon}, {area.max_lat}]"
    report_text = (
        f"Vegetation index anomaly detected: delta={delta_ndvi_scale:.4f} "
        f"({severity}). Bounding box: {area_str}. "
        "All 3 verification subagents passed."
    )

    return ChangeFlag(
        area=area,
        detected_at=datetime.now(timezone.utc),
        index_type="NDVI",
        delta_ndvi_scale=delta_ndvi_scale,
        severity=severity,
        report_text=report_text,
    )
