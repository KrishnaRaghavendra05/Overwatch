import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


# compute ndvi for single date
def compute_ndvi(
    nir: FloatArray,  # raw reflectance scale (confirm 0-1 vs 0-10000 in Phase 1)
    red: FloatArray,  # raw reflectance scale (confirm 0-1 vs 0-10000 in Phase 1)
) -> FloatArray:  # ndvi, -1..1 range
    raise NotImplementedError


# compute ndwi for single date
def compute_ndwi(
    green: FloatArray,  # raw reflectance scale (confirm 0-1 vs 0-10000 in Phase 1)
    nir: FloatArray,  # raw reflectance scale (confirm 0-1 vs 0-10000 in Phase 1)
) -> FloatArray:  # ndwi, -1..1 range
    raise NotImplementedError


# diff two dates, spit raw ndvi change number
def compute_ndvi_delta(
    before_nir: FloatArray,  # raw reflectance scale
    before_red: FloatArray,  # raw reflectance scale
    after_nir: FloatArray,  # raw reflectance scale
    after_red: FloatArray,  # raw reflectance scale
) -> FloatArray:  # ndvi_delta, -2..2 range
    raise NotImplementedError


# diff two dates, spit raw ndwi change number
def compute_ndwi_delta(
    before_green: FloatArray,  # raw reflectance scale
    before_nir: FloatArray,  # raw reflectance scale
    after_green: FloatArray,  # raw reflectance scale
    after_nir: FloatArray,  # raw reflectance scale
) -> FloatArray:  # ndwi_delta, -2..2 range
    raise NotImplementedError
