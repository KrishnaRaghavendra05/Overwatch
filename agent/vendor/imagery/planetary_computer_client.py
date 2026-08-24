import logging

from agent.models.imagery import ImageryRequest, ImageryResponse

logger = logging.getLogger(__name__)

# PC STAC client — auth method and band scale confirmed in Phase 1
# Provider: Microsoft Planetary Computer (planetarycomputer.microsoft.com)
# Auth: token-based — confirm exact auth flow against live endpoint in Phase 1
# Docs: https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/
# TODO Phase 1: fill in real shapes after confirming against live response


# fetch imagery from planetary computer stac for given request
def fetch_imagery(
    request: ImageryRequest,
) -> ImageryResponse:
    logger.info(
        "fetch_imagery called: area=%s date_range=%s collection=%s",
        request.area,
        request.date_range,
        request.collection,
    )
    raise NotImplementedError
