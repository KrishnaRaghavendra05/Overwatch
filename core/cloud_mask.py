import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]

# build bool mask — True where pixel unreliable (cloud or shadow)
def build_cloud_mask(
    scl_band: NDArray[np.uint8],  # Sentinel-2 SCL category code, 0-11
) -> NDArray[np.bool_]:  # True = unreliable pixel
    raise NotImplementedError


# fraction of unreliable pixels, not percentage
def unreliable_pixel_fraction(
    mask: NDArray[np.bool_],
) -> float:  # cloud_pct_0_1, 0.0-1.0 range (not 0-100)
    raise NotImplementedError
