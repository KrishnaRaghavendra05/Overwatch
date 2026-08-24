import logging
import sqlite3

from agent.config import DASHBOARD_DB_PATH

logger = logging.getLogger(__name__)

# schema: one flags table tracks all filed and retracted reports
# columns: record_id, area_json, index_type, delta_ndvi_scale, severity,
#          status, approved_by, approved_at, action, written_at


# get sqlite connection to dashboard db
def get_connection() -> sqlite3.Connection:
    logger.info("db connect: path=%s", DASHBOARD_DB_PATH)
    raise NotImplementedError


# create tables if not exist
def init_db() -> None:
    logger.info("db init: path=%s", DASHBOARD_DB_PATH)
    raise NotImplementedError
