import logging

logger = logging.getLogger(__name__)

# seed reproducible demo data — explicit seed per AGENTS.MD determinism rule
# real sample data selection deferred to Phase 1 once imagery source confirmed


# generate seeded sample data for demo
def seed(seed_value: int = 42) -> None:
    logger.info("seed: seed_value=%s", seed_value)
    raise NotImplementedError


if __name__ == "__main__":
    seed()
