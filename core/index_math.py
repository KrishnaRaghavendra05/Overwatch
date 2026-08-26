import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


# compute ndvi for single date
def compute_ndvi(
    nir: FloatArray,  # raw reflectance scale
    red: FloatArray,  # raw reflectance scale
) -> FloatArray:  # ndvi, -1..1 range
    denom = nir + red
    safe_denom = np.where(denom == 0.0, 1e-10, denom)
    raw = (nir - red) / safe_denom
    return np.clip(np.where(denom == 0.0, 0.0, raw), -1.0, 1.0)


# compute ndwi for single date
def compute_ndwi(
    green: FloatArray,  # raw reflectance scale
    nir: FloatArray,  # raw reflectance scale
) -> FloatArray:  # ndwi, -1..1 range
    denom = green + nir
    safe_denom = np.where(denom == 0.0, 1e-10, denom)
    raw = (green - nir) / safe_denom
    return np.clip(np.where(denom == 0.0, 0.0, raw), -1.0, 1.0)


# diff two dates, spit raw ndvi change number
def compute_ndvi_delta(
    before_nir: FloatArray,  # raw reflectance scale
    before_red: FloatArray,  # raw reflectance scale
    after_nir: FloatArray,  # raw reflectance scale
    after_red: FloatArray,  # raw reflectance scale
) -> FloatArray:  # ndvi_delta, -2..2 range
    ndvi_before = compute_ndvi(before_nir, before_red)
    ndvi_after = compute_ndvi(after_nir, after_red)
    return np.clip(ndvi_after - ndvi_before, -2.0, 2.0)


# diff two dates, spit raw ndwi change number
def compute_ndwi_delta(
    before_green: FloatArray,  # raw reflectance scale
    before_nir: FloatArray,  # raw reflectance scale
    after_green: FloatArray,  # raw reflectance scale
    after_nir: FloatArray,  # raw reflectance scale
) -> FloatArray:  # ndwi_delta, -2..2 range
    ndwi_before = compute_ndwi(before_green, before_nir)
    ndwi_after = compute_ndwi(after_green, after_nir)
    return np.clip(ndwi_after - ndwi_before, -2.0, 2.0)
