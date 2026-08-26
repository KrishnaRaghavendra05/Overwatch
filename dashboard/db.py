import logging
import sqlite3

from agent.config import DASHBOARD_DB_PATH

logger = logging.getLogger(__name__)

# schema: one flags table tracks all filed and retracted reports
# columns: record_id, area_json, index_type, delta_ndvi_scale, severity,
#          report_text, status, approved_by, approved_at, action, written_at

_CREATE_FLAGS_TABLE = """
CREATE TABLE IF NOT EXISTS flags (
    record_id       TEXT PRIMARY KEY,
    area_json       TEXT NOT NULL,
    index_type      TEXT NOT NULL,
    delta_ndvi_scale REAL NOT NULL,
    severity        TEXT NOT NULL,
    report_text     TEXT NOT NULL,
    status          TEXT NOT NULL,
    approved_by     TEXT NOT NULL,
    approved_at     TEXT NOT NULL,
    action          TEXT NOT NULL,
    written_at      TEXT NOT NULL
)
"""


# get sqlite connection to dashboard db
def get_connection() -> sqlite3.Connection:
    logger.info("db connect: path=%s", DASHBOARD_DB_PATH)
    DASHBOARD_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DASHBOARD_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# create tables if not exist
def init_db() -> None:
    logger.info("db init: path=%s", DASHBOARD_DB_PATH)
    conn = get_connection()
    try:
        conn.execute(_CREATE_FLAGS_TABLE)
        conn.commit()
    finally:
        conn.close()
