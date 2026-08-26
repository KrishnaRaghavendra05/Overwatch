import hashlib
import json
import logging
from datetime import date, datetime

import numpy as np

from agent.config import CACHE_DIR
from agent.models.imagery import (
    BoundingBox,
    DateRange,
    ImageryResponse,
    SpectralBands,
)

logger = logging.getLogger(__name__)


def _cache_key(area: BoundingBox, date_range: DateRange) -> str:
    key_str = (
        f"{area.min_lon}_{area.min_lat}_{area.max_lon}_{area.max_lat}_"
        f"{date_range.start}_{date_range.end}"
    )
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:16]


def _save_to_cache(response: ImageryResponse, date_range: DateRange) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(response.area, date_range)
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(mode="json"), f, indent=2)
    logger.info("Seeded cached response at %s (key=%s)", cache_file, key)


# generate seeded sample data for demo
def seed(seed_value: int = 42) -> None:
    np.random.seed(seed_value)
    logger.info("seed: seed_value=%s", seed_value)

    # --- Scenario 1: Severe Crop Stress (Iowa Cornfield) ---
    area_crop = BoundingBox(
        min_lon=-93.55, min_lat=42.01, max_lon=-93.50, max_lat=42.05
    )
    # Before: June 1, 2026 (Healthy vegetation)
    d1_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    resp_crop_before = ImageryResponse(
        request_id="scen1_crop_before",
        acquired=datetime(2026, 6, 1, 10, 30),
        area=area_crop,
        bands=SpectralBands(
            nir_raw=[[0.82 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.12 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.25 for _ in range(5)] for _ in range(5)],
            scl_raw=[[4 for _ in range(5)] for _ in range(5)],  # 4 = Vegetation
        ),
        cloud_cover_pct_0_100=1.2,
        description="Iowa Sector 4 - Healthy Corn Canopy",
    )
    _save_to_cache(resp_crop_before, d1_before)

    # After: July 15, 2026 (Severe drought damage)
    d1_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))
    resp_crop_after = ImageryResponse(
        request_id="scen1_crop_after",
        acquired=datetime(2026, 7, 15, 10, 30),
        area=area_crop,
        bands=SpectralBands(
            nir_raw=[[0.30 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.45 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.22 for _ in range(5)] for _ in range(5)],
            scl_raw=[[5 for _ in range(5)] for _ in range(5)],  # 5 = Bare/dry soil
        ),
        cloud_cover_pct_0_100=2.0,
        description="Iowa Sector 4 - Severe Crop Desiccation",
    )
    _save_to_cache(resp_crop_after, d1_after)

    # --- Scenario 2: Cloud False Positive (Amazon Basin) ---
    area_cloud = BoundingBox(
        min_lon=-62.10, min_lat=-3.45, max_lon=-62.05, max_lat=-3.40
    )
    d2_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    resp_cloud_before = ImageryResponse(
        request_id="scen2_cloud_before",
        acquired=datetime(2026, 6, 1, 14, 0),
        area=area_cloud,
        bands=SpectralBands(
            nir_raw=[[0.85 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.10 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.20 for _ in range(5)] for _ in range(5)],
            scl_raw=[[4 for _ in range(5)] for _ in range(5)],
        ),
        cloud_cover_pct_0_100=0.5,
        description="Amazon Sector 12 - Intact Rainforest",
    )
    _save_to_cache(resp_cloud_before, d2_before)

    # After: Cloud Shadow causing false NDVI drop
    d2_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))
    resp_cloud_after = ImageryResponse(
        request_id="scen2_cloud_after",
        acquired=datetime(2026, 7, 15, 14, 0),
        area=area_cloud,
        bands=SpectralBands(
            nir_raw=[[0.20 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.25 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.18 for _ in range(5)] for _ in range(5)],
            # SCL with cloud shadows (3) and clouds (8, 9)
            scl_raw=[
                [3, 3, 4, 4, 4],
                [3, 8, 9, 4, 4],
                [3, 8, 9, 4, 4],
                [4, 4, 4, 4, 4],
                [4, 4, 4, 4, 4],
            ],
        ),
        cloud_cover_pct_0_100=35.0,
        description="Amazon Sector 12 - Cumulus Shadow Artifact",
    )
    _save_to_cache(resp_cloud_after, d2_after)

    # --- Scenario 3: Ambiguous Thin Haze / Smoke (California Orchard) ---
    area_haze = BoundingBox(
        min_lon=-119.80, min_lat=36.70, max_lon=-119.75, max_lat=36.75
    )
    d3_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    resp_haze_before = ImageryResponse(
        request_id="scen3_haze_before",
        acquired=datetime(2026, 6, 1, 18, 15),
        area=area_haze,
        bands=SpectralBands(
            nir_raw=[[0.78 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.15 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.28 for _ in range(5)] for _ in range(5)],
            scl_raw=[[4 for _ in range(5)] for _ in range(5)],
        ),
        cloud_cover_pct_0_100=0.0,
        description="Fresno Orchard - Healthy Canopy",
    )
    _save_to_cache(resp_haze_before, d3_before)

    d3_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))
    resp_haze_after = ImageryResponse(
        request_id="scen3_haze_after",
        acquired=datetime(2026, 7, 15, 18, 15),
        area=area_haze,
        bands=SpectralBands(
            nir_raw=[[0.48 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.32 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.25 for _ in range(5)] for _ in range(5)],
            # SCL showing thin cirrus/smoke (10) across 20% of pixels
            scl_raw=[
                [10, 10, 4, 4, 4],
                [10, 10, 10, 4, 4],
                [4, 4, 4, 4, 4],
                [4, 4, 4, 4, 4],
                [4, 4, 4, 4, 4],
            ],
        ),
        cloud_cover_pct_0_100=18.0,
        description="Fresno Orchard - Borderline Drop with Wildfire Haze",
    )
    _save_to_cache(resp_haze_after, d3_after)

    # --- Scenario 4: Flood Inundation (Assam Basin) ---
    area_flood = BoundingBox(min_lon=92.50, min_lat=26.20, max_lon=92.55, max_lat=26.25)
    d4_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    resp_flood_before = ImageryResponse(
        request_id="scen4_flood_before",
        acquired=datetime(2026, 6, 1, 5, 0),
        area=area_flood,
        bands=SpectralBands(
            nir_raw=[[0.72 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.18 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.22 for _ in range(5)] for _ in range(5)],
            scl_raw=[[4 for _ in range(5)] for _ in range(5)],
        ),
        cloud_cover_pct_0_100=3.0,
        description="Brahmaputra Floodplain - Pre-monsoon Cropland",
    )
    _save_to_cache(resp_flood_before, d4_before)

    d4_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))
    resp_flood_after = ImageryResponse(
        request_id="scen4_flood_after",
        acquired=datetime(2026, 7, 15, 5, 0),
        area=area_flood,
        bands=SpectralBands(
            nir_raw=[[0.12 for _ in range(5)] for _ in range(5)],
            red_raw=[[0.14 for _ in range(5)] for _ in range(5)],
            green_raw=[[0.68 for _ in range(5)] for _ in range(5)],
            scl_raw=[[6 for _ in range(5)] for _ in range(5)],  # 6 = Water
        ),
        cloud_cover_pct_0_100=4.5,
        description="Brahmaputra Floodplain - Severe Inundation",
    )
    _save_to_cache(resp_flood_after, d4_after)

    logger.info("Successfully seeded 4 demo scenarios (8 image tiles) into cache.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
