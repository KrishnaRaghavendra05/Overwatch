import logging

from agent.models.imagery import ImageryResponse

logger = logging.getLogger(__name__)

# step 4 verification: disprove signal via cloud/shadow contamination
# concurrent orchestration wired in Phase 3


# True if imagery reliable (cloud fraction below threshold)
def run_cloud_check(
    response: ImageryResponse,
) -> bool:
    logger.info("cloud_check: request_id=%s", response.request_id)
    raise NotImplementedError
