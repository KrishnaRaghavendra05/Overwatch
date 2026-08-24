import logging

from agent.models.imagery import BoundingBox, DateRange

logger = logging.getLogger(__name__)

# step 4 verification: disprove signal via confounding weather events
# concurrent orchestration wired in Phase 3


# True if no confounding weather event found for area/period
def run_weather_check(
    area: BoundingBox,
    date_range: DateRange,
) -> bool:
    logger.info("weather_check: area=%s date_range=%s", area, date_range)
    raise NotImplementedError
