import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


# build bool mask — True where pixel unreliable (cloud or shadow)
def build_cloud_mask(
    scl_band: NDArray[np.uint8],  # Sentinel-2 SCL category code, 0-11
) -> NDArray[np.bool_]:  # True = unreliable pixel
    # 0=No Data, 1=Saturated/Defective, 3=Shadow, 8=Cloud Med, 9=Cloud High, 10=Cirrus
    unreliable_classes = (0, 1, 3, 8, 9, 10)
    return np.isin(scl_band, unreliable_classes)


# fraction of unreliable pixels, not percentage
def unreliable_pixel_fraction(
    mask: NDArray[np.bool_],
) -> float:  # cloud_pct_0_1, 0.0-1.0 range (not 0-100)
    if mask.size == 0:
        return 0.0
    return float(np.mean(mask))
