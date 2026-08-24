import logging

from agent.models.imagery import BoundingBox, DateRange, ImageryResponse
from agent.services.cache import get_or_fetch

logger = logging.getLogger(__name__)

# MCP tool entrypoint for step 2 — TrueForge calls this to fetch imagery
# MCP registration shape depends on TrueForge SDK — confirm in Phase 1
# call chain: cache -> vendor client (never call vendor directly)


# fetch imagery for area and date window, cache-first
def fetch_imagery_tool(
    area: BoundingBox,
    date_range: DateRange,
) -> ImageryResponse:
    logger.info(
        "fetch_imagery_tool: area=%s date_range=%s",
        area,
        date_range,
    )
    return get_or_fetch(area, date_range)
