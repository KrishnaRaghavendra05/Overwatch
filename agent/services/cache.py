import hashlib
import json
import logging
from datetime import datetime

from agent.config import CACHE_DIR
from agent.models.imagery import (
    BoundingBox,
    DateRange,
    ImageryResponse,
    SpectralBands,
)

logger = logging.getLogger(__name__)


# derive deterministic hash key for bbox and date range
def _cache_key(area: BoundingBox, date_range: DateRange) -> str:
    key_str = (
        f"{area.min_lon}_{area.min_lat}_{area.max_lon}_{area.max_lat}_"
        f"{date_range.start}_{date_range.end}"
    )
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:16]


# check cache first, fallback to mock generator if not found
def get_or_fetch(
    area: BoundingBox,
    date_range: DateRange,
) -> ImageryResponse:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(area, date_range)
    cache_file = CACHE_DIR / f"{key}.json"

    if cache_file.exists():
        logger.info("CACHE HIT for key=%s (area=%s, dates=%s)", key, area, date_range)
        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)
            return ImageryResponse.model_validate(data)

    logger.info("CACHE MISS for key=%s. Generating synthetic band data.", key)
    # Default synthetic healthy field tile (5x5 pixels)
    bands = SpectralBands(
        nir_raw=[[0.75 for _ in range(5)] for _ in range(5)],
        red_raw=[[0.15 for _ in range(5)] for _ in range(5)],
        green_raw=[[0.30 for _ in range(5)] for _ in range(5)],
        scl_raw=[[4 for _ in range(5)] for _ in range(5)],  # 4 = Vegetation
    )
    response = ImageryResponse(
        request_id=f"req_{key}",
        acquired=datetime.combine(date_range.end, datetime.min.time()),
        area=area,
        bands=bands,
        cloud_cover_pct_0_100=0.0,
        description="Generated synthetic baseline imagery tile",
    )

    # Save to disk cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(mode="json"), f, indent=2)

    return response
