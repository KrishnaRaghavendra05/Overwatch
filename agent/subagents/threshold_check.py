import logging

logger = logging.getLogger(__name__)

# step 4 verification: disprove signal via threshold comparison
# concurrent orchestration wired in Phase 3


# True if delta crosses configured severity threshold
def run_threshold_check(
    delta_ndvi_scale: float,  # ndvi_delta or ndwi_delta, native -2..2 scale
) -> bool:
    logger.info("threshold_check: delta_ndvi_scale=%s", delta_ndvi_scale)
    raise NotImplementedError
