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
    # TODO Phase 1: confirm band naming convention with chosen provider
    # TODO Phase 1: confirm reflectance scale — 0-1 or 0-10000
    nir_raw: list[list[float]]  # near-infrared band, raw provider scale
    red_raw: list[list[float]]  # red band, raw provider scale
    green_raw: list[list[float]]  # green band, raw provider scale


# full imagery response from provider or cache
class ImageryResponse(BaseModel):
    request_id: str
    acquired: datetime
    area: BoundingBox
    bands: SpectralBands
    # TODO Phase 1: confirm field name and unit from live provider response
    # could be percentage (0-100) or fraction (0-1) — name assumes percentage
    cloud_cover_pct_0_100: float
