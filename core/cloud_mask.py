import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

# Sentinel-2 SCL codes that mean pixel is unreliable
# 0 = no data, 1 = saturated/defective, 2 = dark area / shadow,
# 3 = cloud shadow, 8 = cloud medium prob, 9 = cloud high prob, 10 = cirrus
_UNRELIABLE_SCL_CODES: set[int] = {0, 1, 2, 3, 8, 9, 10}


# build bool mask — True where pixel unreliable (cloud or shadow)
def build_cloud_mask(
    scl_band: NDArray[np.uint8],  # Sentinel-2 SCL category code, 0-11
) -> NDArray[np.bool_]:  # True = unreliable pixel
    return np.isin(scl_band, list(_UNRELIABLE_SCL_CODES))


# fraction of unreliable pixels, not percentage
def unreliable_pixel_fraction(
    mask: NDArray[np.bool_],
) -> float:  # cloud_pct_0_1, 0.0-1.0 range (not 0-100)
    if mask.size == 0:
        return 0.0
    return float(np.count_nonzero(mask) / mask.size)
