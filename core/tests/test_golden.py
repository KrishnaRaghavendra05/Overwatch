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

from core.index_math import compute_ndvi_delta

FloatArray = NDArray[np.float64]

# ---- shared fixtures -------------------------------------------------------

# Uniform 2×2 before arrays: healthy vegetation (high NIR, low RED)
BEFORE_NIR: FloatArray = np.full((2, 2), 0.8, dtype=np.float64)
BEFORE_RED: FloatArray = np.full((2, 2), 0.2, dtype=np.float64)

# Uniform 2×2 after arrays: stressed vegetation (NIR drops, RED rises)
AFTER_NIR: FloatArray = np.full((2, 2), 0.4, dtype=np.float64)
AFTER_RED: FloatArray = np.full((2, 2), 0.4, dtype=np.float64)

# Hand-computed expected delta (see module docstring for derivation)
EXPECTED_NDVI_DELTA: FloatArray = np.full((2, 2), -0.6, dtype=np.float64)

# Tolerance: exact arithmetic on simple fractions, so tight tolerance is valid.
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
