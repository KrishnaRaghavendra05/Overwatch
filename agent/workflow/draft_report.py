import logging

from agent.models.dashboard import ChangeFlag
from agent.models.imagery import BoundingBox

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
    raise NotImplementedError
