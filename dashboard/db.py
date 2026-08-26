import logging
import sqlite3

from agent.config import DASHBOARD_DB_PATH

logger = logging.getLogger(__name__)


# get sqlite connection to dashboard db
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DASHBOARD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# create tables if not exist
def init_db() -> None:
    logger.info("db init: path=%s", DASHBOARD_DB_PATH)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                record_id TEXT PRIMARY KEY,
                area_json TEXT NOT NULL,
                index_type TEXT NOT NULL,
                delta_ndvi_scale REAL NOT NULL,
                severity TEXT NOT NULL,
                report_text TEXT NOT NULL,
                status TEXT NOT NULL,
                approved_by TEXT NOT NULL,
                approved_at TEXT NOT NULL,
                action TEXT NOT NULL,
                written_at TEXT NOT NULL
            )
        """)
        conn.commit()
