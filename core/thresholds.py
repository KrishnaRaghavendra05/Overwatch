# severity thresholds — all values in native NDVI/NDWI scale (-1..1), not percentage

# crop stress floor: ndvi drop this big flags severe damage
NDVI_DELTA_SEVERE_NDVI_SCALE: float = -0.20

# crop stress: moderate warning level
NDVI_DELTA_MODERATE_NDVI_SCALE: float = -0.10

# flooding: ndwi rise this big flags water extent change
NDWI_DELTA_FLOOD_NDWI_SCALE: float = 0.15

# reject imagery if cloud fraction exceeds this (0.0-1.0, not percent)
CLOUD_FRACTION_REJECT_THRESHOLD_0_1: float = 0.20


# check if delta crosses threshold — True means signal real enough to investigate
def delta_crosses_threshold(
    delta: float,  # ndvi_delta or ndwi_delta, native -2..2 scale
    threshold: float,  # from constants above, native -1..1 scale
) -> bool:
    if threshold < 0.0:
        return delta <= threshold
    return delta >= threshold
