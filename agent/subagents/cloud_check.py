import logging

import numpy as np

from agent.models.imagery import ImageryResponse
from agent.models.verification import SubagentResult
from core.cloud_mask import build_cloud_mask, unreliable_pixel_fraction
from core.thresholds import CLOUD_FRACTION_REJECT_THRESHOLD_0_1

logger = logging.getLogger(__name__)


# verify imagery is not invalidated by clouds, shadows, or smoke
def run_cloud_check(
    response: ImageryResponse,
) -> SubagentResult:
    logger.info("cloud_check: running on request_id=%s", response.request_id)

    # If SCL band is available, compute spatial cloud/shadow mask
    if response.bands.scl_raw:
        scl_array = np.array(response.bands.scl_raw, dtype=np.uint8)
        mask = build_cloud_mask(scl_array)
        fraction = unreliable_pixel_fraction(mask)
        cirrus_pixels = int(np.sum(scl_array == 10))
        shadow_pixels = int(np.sum(scl_array == 3))
    else:
        # Fallback to provider metadata cloud percentage (0-100 scale -> 0-1)
        fraction = response.cloud_cover_pct_0_100 / 100.0
        cirrus_pixels = 0
        shadow_pixels = 0

    # Ambiguity case: thin haze/cirrus (10-25% unreliable pixels)
    if (
        0.10 <= fraction <= CLOUD_FRACTION_REJECT_THRESHOLD_0_1 + 0.05
        and cirrus_pixels > 0
    ):
        return SubagentResult(
            check_name="cloud_shadow",
            passed=True,
            confidence=0.55,
            is_ambiguous=True,
            details=(
                f"Thin haze/cirrus detected ({fraction:.1%} pixels unreliable, "
                f"{cirrus_pixels} cirrus pixels). Needs human disambiguation."
            ),
            metrics={
                "cloud_fraction": fraction,
                "cirrus_pixels": cirrus_pixels,
                "shadow_pixels": shadow_pixels,
                "threshold": CLOUD_FRACTION_REJECT_THRESHOLD_0_1,
            },
        )

    # Severe cloud/shadow contamination case (> 20%) -> Disprove signal
    if fraction > CLOUD_FRACTION_REJECT_THRESHOLD_0_1:
        return SubagentResult(
            check_name="cloud_shadow",
            passed=False,
            confidence=0.92,
            is_ambiguous=False,
            details=(
                f"Cloud/shadow contamination too high: {fraction:.1%} unreliable "
                f"pixels exceeds {CLOUD_FRACTION_REJECT_THRESHOLD_0_1:.0%} limit."
            ),
            metrics={
                "cloud_fraction": fraction,
                "shadow_pixels": shadow_pixels,
                "threshold": CLOUD_FRACTION_REJECT_THRESHOLD_0_1,
            },
        )

    # Clean imagery case (<= 10% clouds) -> Passed
    return SubagentResult(
        check_name="cloud_shadow",
        passed=True,
        confidence=0.95,
        is_ambiguous=False,
        details=f"Clean optical scene: {fraction:.1%} cloud/shadow fraction.",
        metrics={
            "cloud_fraction": fraction,
            "shadow_pixels": shadow_pixels,
            "threshold": CLOUD_FRACTION_REJECT_THRESHOLD_0_1,
        },
    )
