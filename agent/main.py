"""CLI entrypoint — thin wrapper around agent.runner."""

import argparse
import logging
from datetime import date

from agent.models.imagery import BoundingBox, DateRange
from agent.runner import run_scenario
from scripts.seed_sample_data import seed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("overwatch.agent")

SCENARIOS = {
    "crop_damage": {
        "name": "Iowa Corn Canopy (Severe Desiccation / Crop Stress)",
        "area": BoundingBox(
            min_lon=-93.55,
            min_lat=42.01,
            max_lon=-93.50,
            max_lat=42.05,
        ),
        "d_before": DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2)),
        "d_after": DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16)),
        "index_type": "NDVI",
    },
    "cloud_false_positive": {
        "name": "Amazon Rainforest Sector 12 (Cloud Shadow Artifact)",
        "area": BoundingBox(
            min_lon=-62.10,
            min_lat=-3.45,
            max_lon=-62.05,
            max_lat=-3.40,
        ),
        "d_before": DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2)),
        "d_after": DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16)),
        "index_type": "NDVI",
    },
    "ambiguous_haze": {
        "name": "California Orchard (Wildfire Haze Disambiguation)",
        "area": BoundingBox(
            min_lon=-119.80,
            min_lat=36.70,
            max_lon=-119.75,
            max_lat=36.75,
        ),
        "d_before": DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2)),
        "d_after": DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16)),
        "index_type": "NDVI",
    },
    "flood": {
        "name": "Assam Brahmaputra Floodplain (Monsoon Inundation)",
        "area": BoundingBox(
            min_lon=92.50,
            min_lat=26.20,
            max_lon=92.55,
            max_lat=26.25,
        ),
        "d_before": DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2)),
        "d_after": DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16)),
        "index_type": "NDWI",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Overwatch Change Detection Agent")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="crop_damage",
        help="Demo scenario to run",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without interactive confirmation prompts",
    )
    parser.add_argument(
        "--approver",
        default="Kaamil Hifzaan",
        help="Approver identity for human gate",
    )
    args = parser.parse_args()

    seed(42)

    cfg = SCENARIOS[args.scenario]
    run_scenario(
        name=cfg["name"],
        area=cfg["area"],
        d_before=cfg["d_before"],
        d_after=cfg["d_after"],
        index_type=cfg["index_type"],
        interactive=not args.non_interactive,
        approver=args.approver,
    )


if __name__ == "__main__":
    main()
