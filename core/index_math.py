import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

# tiny guard against 0/0 on dead pixels
_EPS: float = 1e-10


# compute ndvi for single date
def compute_ndvi(
    nir: FloatArray,  # reflectance, any consistent scale (0-1 or 0-10000)
    red: FloatArray,  # reflectance, same scale as nir
) -> FloatArray:  # ndvi, -1..1 range
    denom = nir + red
    safe_denom = np.where(np.abs(denom) < _EPS, _EPS, denom)
    return (nir - red) / safe_denom


# compute ndwi for single date
def compute_ndwi(
    green: FloatArray,  # reflectance, any consistent scale
    nir: FloatArray,  # reflectance, same scale as green
) -> FloatArray:  # ndwi, -1..1 range
    denom = green + nir
    safe_denom = np.where(np.abs(denom) < _EPS, _EPS, denom)
    return (green - nir) / safe_denom


# diff two dates, spit raw ndvi change number
def compute_ndvi_delta(
    before_nir: FloatArray,  # reflectance
    before_red: FloatArray,  # reflectance
    after_nir: FloatArray,  # reflectance
    after_red: FloatArray,  # reflectance
) -> FloatArray:  # ndvi_delta, -2..2 range
    return compute_ndvi(after_nir, after_red) - compute_ndvi(before_nir, before_red)


# diff two dates, spit raw ndwi change number
def compute_ndwi_delta(
    before_green: FloatArray,  # reflectance
    before_nir: FloatArray,  # reflectance
    after_green: FloatArray,  # reflectance
    after_nir: FloatArray,  # reflectance
) -> FloatArray:  # ndwi_delta, -2..2 range
    return compute_ndwi(after_green, after_nir) - compute_ndwi(before_green, before_nir)
