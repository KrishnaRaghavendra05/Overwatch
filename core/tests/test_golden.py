"""
test_golden.py — regression baseline for NDVI delta math.

Fixture design rationale
------------------------
We use uniform 2×2 arrays so the expected value is fully hand-computable
without any floating-point approximation surprises.

  NDVI = (NIR - RED) / (NIR + RED)

Before image:
  NIR = 0.8, RED = 0.2  →  NDVI_before = (0.8 - 0.2) / (0.8 + 0.2) = 0.6 / 1.0 = 0.600

After image (simulating severe crop stress — large NIR drop, RED rise):
  NIR = 0.4, RED = 0.4  →  NDVI_after  = (0.4 - 0.4) / (0.4 + 0.4) = 0.0 / 0.8 = 0.000

Delta:
  ndvi_delta = NDVI_after - NDVI_before = 0.000 - 0.600 = -0.600

This delta (-0.6) comfortably crosses the NDVI_DELTA_SEVERE_NDVI_SCALE threshold
(-0.20).

IMPORTANT: all reflectance values here use the 0–1 scale. If the chosen imagery
provider returns 0–10000 scale, these fixtures must be updated. Confirm scale
against a live response in Phase 1.
"""

import numpy as np
from numpy.typing import NDArray

from core.cloud_mask import build_cloud_mask, unreliable_pixel_fraction
from core.index_math import (
    compute_ndvi,
    compute_ndvi_delta,
    compute_ndwi,
    compute_ndwi_delta,
)
from core.thresholds import (
    CLOUD_FRACTION_REJECT_THRESHOLD_0_1,
    NDVI_DELTA_MODERATE_NDVI_SCALE,
    NDVI_DELTA_SEVERE_NDVI_SCALE,
    NDWI_DELTA_FLOOD_NDWI_SCALE,
    delta_crosses_threshold,
)

FloatArray = NDArray[np.float64]

# ---- shared fixtures -------------------------------------------------------

# Uniform 2×2 before arrays: healthy vegetation (high NIR, low RED)
BEFORE_NIR: FloatArray = np.full((2, 2), 0.8, dtype=np.float64)
BEFORE_RED: FloatArray = np.full((2, 2), 0.2, dtype=np.float64)

# Uniform 2×2 after arrays: stressed vegetation (NIR drops, RED rises)
AFTER_NIR: FloatArray = np.full((2, 2), 0.4, dtype=np.float64)
AFTER_RED: FloatArray = np.full((2, 2), 0.4, dtype=np.float64)

# Hand-computed expected delta: 0.000 - 0.600 = -0.600
EXPECTED_NDVI_DELTA: FloatArray = np.full((2, 2), -0.6, dtype=np.float64)

DELTA_TOLERANCE: float = 1e-9


# ---- tests -----------------------------------------------------------------


def test_ndvi_delta_shape() -> None:
    """Output array must have same spatial shape as the input bands."""
    result = compute_ndvi_delta(BEFORE_NIR, BEFORE_RED, AFTER_NIR, AFTER_RED)
    assert result.shape == BEFORE_NIR.shape


def test_ndvi_delta_known_value() -> None:
    """Delta must match the hand-computed expected value within tight tolerance."""
    result = compute_ndvi_delta(BEFORE_NIR, BEFORE_RED, AFTER_NIR, AFTER_RED)
    np.testing.assert_allclose(result, EXPECTED_NDVI_DELTA, atol=DELTA_TOLERANCE)


def test_ndvi_delta_range() -> None:
    """NDVI delta must stay within the theoretical -2 to 2 range."""
    result = compute_ndvi_delta(BEFORE_NIR, BEFORE_RED, AFTER_NIR, AFTER_RED)
    assert np.all(result >= -2.0), "delta below -2 — formula error"
    assert np.all(result <= 2.0), "delta above 2 — formula error"


def test_single_date_ndvi() -> None:
    """Single date NDVI must be exactly in [-1, 1] range."""
    ndvi = compute_ndvi(BEFORE_NIR, BEFORE_RED)
    np.testing.assert_allclose(ndvi, np.full((2, 2), 0.6), atol=DELTA_TOLERANCE)


def test_ndwi_and_delta() -> None:
    """NDWI calculation for water extent change."""
    green = np.full((2, 2), 0.7, dtype=np.float64)
    nir = np.full((2, 2), 0.3, dtype=np.float64)
    ndwi = compute_ndwi(green, nir)
    np.testing.assert_allclose(ndwi, np.full((2, 2), 0.4), atol=DELTA_TOLERANCE)

    ndwi_delta = compute_ndwi_delta(green, nir, green * 1.2, nir * 0.5)
    assert np.all(ndwi_delta >= -2.0)
    assert np.all(ndwi_delta <= 2.0)


def test_zero_denominator_safe() -> None:
    """Zero reflectance pixels must not crash or produce NaNs."""
    zeros = np.zeros((2, 2), dtype=np.float64)
    ndvi = compute_ndvi(zeros, zeros)
    assert not np.isnan(ndvi).any()
    assert np.all(ndvi == 0.0)


def test_cloud_masking() -> None:
    """SCL mask flags clouds, shadows, and calculates fraction correctly."""
    # 4=veg, 3=shadow, 8=cloud_med, 5=bare
    scl = np.array([[4, 3], [8, 5]], dtype=np.uint8)
    mask = build_cloud_mask(scl)
    expected_mask = np.array([[False, True], [True, False]])
    np.testing.assert_array_equal(mask, expected_mask)

    fraction = unreliable_pixel_fraction(mask)
    assert fraction == 0.5


def test_threshold_crossings() -> None:
    """Threshold logic handles negative crop stress and positive flood deltas."""
    # Crop stress: -0.30 is more severe than -0.20 threshold -> True
    assert delta_crosses_threshold(-0.30, NDVI_DELTA_SEVERE_NDVI_SCALE) is True
    assert delta_crosses_threshold(-0.05, NDVI_DELTA_SEVERE_NDVI_SCALE) is False
    assert delta_crosses_threshold(-0.15, NDVI_DELTA_MODERATE_NDVI_SCALE) is True

    # Flood: +0.25 is greater than +0.15 threshold -> True
    assert delta_crosses_threshold(0.25, NDWI_DELTA_FLOOD_NDWI_SCALE) is True
    assert delta_crosses_threshold(0.05, NDWI_DELTA_FLOOD_NDWI_SCALE) is False

    # Cloud fraction threshold
    assert 0.25 > CLOUD_FRACTION_REJECT_THRESHOLD_0_1
