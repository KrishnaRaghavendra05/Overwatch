from datetime import date, datetime

from pydantic import BaseModel


# bounding box for target area
class BoundingBox(BaseModel):
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


# start/end date pair for imagery window
class DateRange(BaseModel):
    start: date
    end: date


# what to fetch
class ImageryRequest(BaseModel):
    area: BoundingBox
    date_range: DateRange
    # e.g. "sentinel-2-l2a" — confirm collection id in Phase 1
    collection: str


# raw spectral bands from provider
class SpectralBands(BaseModel):
    nir_raw: list[list[float]]  # near-infrared band, 0-1 or 0-10000 scale
    red_raw: list[list[float]]  # red band, 0-1 or 0-10000 scale
    green_raw: list[list[float]]  # green band, 0-1 or 0-10000 scale
    scl_raw: list[list[int]] | None = None  # Sentinel-2 SCL (0-11)


# full imagery response from provider or cache
class ImageryResponse(BaseModel):
    request_id: str
    acquired: datetime
    area: BoundingBox
    bands: SpectralBands
    cloud_cover_pct_0_100: float
    description: str | None = None
