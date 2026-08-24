import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# model provider name — stays generic, TrueForge is bring-your-own-model
MODEL_PROVIDER: str = os.environ.get("MODEL_PROVIDER", "")

# api key for chosen model provider
MODEL_API_KEY: str = os.environ.get("MODEL_API_KEY", "")

# daytona sandbox api key
DAYTONA_API_KEY: str = os.environ.get("DAYTONA_API_KEY", "")

# imagery provider credentials
IMAGERY_PROVIDER_KEY: str = os.environ.get("IMAGERY_PROVIDER_KEY", "")
IMAGERY_PROVIDER_URL: str = os.environ.get("IMAGERY_PROVIDER_URL", "")

# local path for imagery fetch cache
CACHE_DIR: Path = Path(os.environ.get("CACHE_DIR", ".cache/imagery"))

# local path for dashboard sqlite db
DASHBOARD_DB_PATH: Path = Path(os.environ.get("DASHBOARD_DB_PATH", "dashboard.db"))
