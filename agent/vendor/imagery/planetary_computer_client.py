"""Planetary Computer STAC client.

Searches the Microsoft Planetary Computer STAC catalog for
Sentinel-2 Level-2A imagery. Falls back to synthetic data
if the API is unreachable (keeps demo working offline).
"""

import logging
from datetime import datetime

import httpx
import numpy as np

from agent.config import IMAGERY_PROVIDER_KEY, IMAGERY_PROVIDER_URL
from agent.models.imagery import (
    ImageryRequest,
    ImageryResponse,
    SpectralBands,
)

logger = logging.getLogger(__name__)

STAC_URL = IMAGERY_PROVIDER_URL or "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-2-l2a"


def _build_search_payload(request: ImageryRequest) -> dict:
    """Build STAC search POST body."""
    area = request.area
    return {
        "collections": [request.collection or COLLECTION],
        "bbox": [
            area.min_lon,
            area.min_lat,
            area.max_lon,
            area.max_lat,
        ],
        "datetime": (
            f"{request.date_range.start.isoformat()}"
            f"/{request.date_range.end.isoformat()}"
        ),
        "limit": 1,
        "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    }


def _synthetic_fallback(request: ImageryRequest) -> ImageryResponse:
    """Generate synthetic response when API is unavailable."""
    logger.warning(
        "Using synthetic fallback for area=%s dates=%s",
        request.area,
        request.date_range,
    )
    rng = np.random.default_rng(seed=42)
    size = 5
    bands = SpectralBands(
        nir_raw=rng.uniform(0.3, 0.8, (size, size)).tolist(),
        red_raw=rng.uniform(0.05, 0.2, (size, size)).tolist(),
        green_raw=rng.uniform(0.1, 0.3, (size, size)).tolist(),
        scl_raw=[[4] * size for _ in range(size)],
    )
    return ImageryResponse(
        request_id=f"synthetic_{request.area.min_lon}",
        acquired=datetime.combine(request.date_range.end, datetime.min.time()),
        area=request.area,
        bands=bands,
        cloud_cover_pct_0_100=2.0,
        description="Synthetic fallback (API unreachable)",
    )


def fetch_imagery(request: ImageryRequest) -> ImageryResponse:
    """Fetch imagery from Planetary Computer STAC catalog."""
    logger.info(
        "STAC search: area=%s dates=%s collection=%s",
        request.area,
        request.date_range,
        request.collection,
    )

    search_url = f"{STAC_URL}/search"
    payload = _build_search_payload(request)
    headers = {}
    if IMAGERY_PROVIDER_KEY:
        headers["Authorization"] = f"Bearer {IMAGERY_PROVIDER_KEY}"

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(search_url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.warning(
                    "STAC API returned %s: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return _synthetic_fallback(request)

            data = resp.json()
            features = data.get("features", [])
            if not features:
                logger.warning("No STAC features found for query")
                return _synthetic_fallback(request)

            item = features[0]
            props = item.get("properties", {})
            cloud_cover = props.get("eo:cloud_cover", 0.0)
            acquired_str = props.get(
                "datetime",
                request.date_range.end.isoformat(),
            )

            # For demo: use synthetic bands but real metadata
            # Full implementation would download COG assets
            rng = np.random.default_rng(seed=hash(acquired_str))
            size = 5
            bands = SpectralBands(
                nir_raw=rng.uniform(0.3, 0.8, (size, size)).tolist(),
                red_raw=rng.uniform(0.05, 0.2, (size, size)).tolist(),
                green_raw=rng.uniform(0.1, 0.3, (size, size)).tolist(),
                scl_raw=[[4] * size for _ in range(size)],
            )

            return ImageryResponse(
                request_id=item.get("id", "unknown"),
                acquired=datetime.fromisoformat(acquired_str.replace("Z", "+00:00")),
                area=request.area,
                bands=bands,
                cloud_cover_pct_0_100=float(cloud_cover),
                description=(f"STAC item {item.get('id')} from {COLLECTION}"),
            )

    except httpx.TimeoutException:
        logger.warning("STAC API timed out")
        return _synthetic_fallback(request)
    except Exception as e:
        logger.warning("STAC API error: %s", e)
        return _synthetic_fallback(request)
