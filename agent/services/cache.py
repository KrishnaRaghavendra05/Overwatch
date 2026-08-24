import logging

from agent.models.imagery import BoundingBox, DateRange, ImageryResponse

logger = logging.getLogger(__name__)

# cache is load-bearing — never fetch same area/date pair twice
# rate-limited public apis will ban on repeat fetches for same data


# check cache first, fetch from vendor only on miss
def get_or_fetch(
    area: BoundingBox,
    date_range: DateRange,
) -> ImageryResponse:
    logger.info(
        "cache lookup: area=%s date_range=%s",
        area,
        date_range,
    )
    raise NotImplementedError
