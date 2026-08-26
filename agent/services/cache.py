import hashlib
import json
import logging
from pathlib import Path

from agent.config import CACHE_DIR
from agent.models.imagery import (
    BoundingBox,
    DateRange,
    ImageryRequest,
    ImageryResponse,
)
from agent.vendor.imagery.planetary_computer_client import fetch_imagery

logger = logging.getLogger(__name__)

# cache is load-bearing — never fetch same area/date pair twice
# rate-limited public apis will ban on repeat fetches for same data


# compute deterministic hash key for area and date window
def _cache_key(area: BoundingBox, date_range: DateRange) -> str:
    coords = f"{area.min_lon}_{area.min_lat}_{area.max_lon}_{area.max_lat}"
    dates = f"{date_range.start}_{date_range.end}"
    payload = f"{coords}_{dates}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


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
    cache_path = Path(CACHE_DIR)
    cache_path.mkdir(parents=True, exist_ok=True)
    key = _cache_key(area, date_range)
    entry_file = cache_path / f"{key}.json"

    if entry_file.exists():
        logger.info("cache hit: key=%s", key)
        data = json.loads(entry_file.read_text(encoding="utf-8"))
        return ImageryResponse.model_validate(data)

    logger.info("cache miss: key=%s, fetching from vendor", key)
    request = ImageryRequest(
        area=area,
        date_range=date_range,
        collection="sentinel-2-l2a",
    )
    response = fetch_imagery(request)
    entry_file.write_text(response.model_dump_json(indent=2), encoding="utf-8")
    return response
