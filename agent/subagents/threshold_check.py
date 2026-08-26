import logging

from agent.models.verification import SubagentResult
from core.thresholds import (
    NDVI_DELTA_MODERATE_NDVI_SCALE,
    NDVI_DELTA_SEVERE_NDVI_SCALE,
    NDWI_DELTA_FLOOD_NDWI_SCALE,
    delta_crosses_threshold,
)

logger = logging.getLogger(__name__)


# verify delta crosses meaningful severity threshold and not background noise
def run_threshold_check(
    delta_val: float,  # ndvi_delta or ndwi_delta (-2..2 scale)
    index_type: str = "NDVI",
) -> SubagentResult:
    logger.info("threshold_check: delta=%s, index_type=%s", delta_val, index_type)

    if index_type == "NDWI":
        # Flooding check
        crosses_flood = delta_crosses_threshold(delta_val, NDWI_DELTA_FLOOD_NDWI_SCALE)
        if crosses_flood:
            return SubagentResult(
                check_name="threshold_check",
                passed=True,
                confidence=0.96,
                is_ambiguous=False,
                details=(
                    f"Severe water extent increase (NDWI delta +{delta_val:.2f} "
                    f">= +{NDWI_DELTA_FLOOD_NDWI_SCALE:.2f})"
                ),
                metrics={
                    "delta": delta_val,
                    "threshold": NDWI_DELTA_FLOOD_NDWI_SCALE,
                    "severity": "severe",
                },
            )
        return SubagentResult(
            check_name="threshold_check",
            passed=False,
            confidence=0.90,
            is_ambiguous=False,
            details=(
                f"NDWI delta +{delta_val:.2f} did not reach flood threshold "
                f"(+{NDWI_DELTA_FLOOD_NDWI_SCALE:.2f})"
            ),
            metrics={
                "delta": delta_val,
                "threshold": NDWI_DELTA_FLOOD_NDWI_SCALE,
                "severity": "none",
            },
        )

    # NDVI Crop Stress / Deforestation check
    crosses_severe = delta_crosses_threshold(delta_val, NDVI_DELTA_SEVERE_NDVI_SCALE)
    crosses_moderate = delta_crosses_threshold(
        delta_val, NDVI_DELTA_MODERATE_NDVI_SCALE
    )

    if crosses_severe:
        return SubagentResult(
            check_name="threshold_check",
            passed=True,
            confidence=0.95,
            is_ambiguous=False,
            details=(
                f"Severe vegetation loss confirmed: NDVI delta {delta_val:.2f} "
                f"<= {NDVI_DELTA_SEVERE_NDVI_SCALE:.2f}"
            ),
            metrics={
                "delta": delta_val,
                "threshold": NDVI_DELTA_SEVERE_NDVI_SCALE,
                "severity": "severe",
            },
        )

    if crosses_moderate:
        return SubagentResult(
            check_name="threshold_check",
            passed=True,
            confidence=0.70,
            is_ambiguous=True,
            details=(
                f"Moderate vegetation drop: NDVI delta {delta_val:.2f} is in "
                f"warning zone ({NDVI_DELTA_MODERATE_NDVI_SCALE:.2f})"
            ),
            metrics={
                "delta": delta_val,
                "threshold": NDVI_DELTA_MODERATE_NDVI_SCALE,
                "severity": "moderate",
            },
        )

    # Below moderate threshold -> Disprove as normal seasonal / sensor noise
    return SubagentResult(
        check_name="threshold_check",
        passed=False,
        confidence=0.92,
        is_ambiguous=False,
        details=(
            f"Delta {delta_val:.2f} is within normal background noise "
            f"(threshold {NDVI_DELTA_MODERATE_NDVI_SCALE:.2f})"
        ),
        metrics={
            "delta": delta_val,
            "threshold": NDVI_DELTA_MODERATE_NDVI_SCALE,
            "severity": "noise",
        },
    )
