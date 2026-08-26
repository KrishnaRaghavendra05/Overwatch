from datetime import datetime, timezone

import pytest

from agent.models.dashboard import ChangeFlag, DashboardWritePayload
from agent.models.imagery import BoundingBox
from dashboard.db import init_db
from dashboard.read import list_flags, read_flag
from dashboard.write import write_flag


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_dashboard.db"
    monkeypatch.setattr("dashboard.db.DASHBOARD_DB_PATH", test_db)
    monkeypatch.setattr("agent.config.DASHBOARD_DB_PATH", test_db)
    init_db()


def test_write_and_read_flag():
    area = BoundingBox(min_lon=10.0, min_lat=20.0, max_lon=10.5, max_lat=20.5)
    flag = ChangeFlag(
        area=area,
        detected_at=datetime.now(timezone.utc),
        index_type="NDVI",
        delta_ndvi_scale=-0.35,
        severity="severe",
        report_text="Severe vegetation anomaly detected",
    )
    payload = DashboardWritePayload(
        flag=flag,
        approved_by="human_reviewer_01",
        approved_at=datetime.now(timezone.utc),
        action="file",
    )

    write_resp = write_flag(payload)
    assert write_resp.verified is True
    assert write_resp.status == "filed"

    read_resp = read_flag(write_resp.record_id)
    assert read_resp.record_id == write_resp.record_id
    assert read_resp.status == "filed"
    assert read_resp.area.min_lon == 10.0

    all_flags = list_flags()
    assert len(all_flags) == 1
    assert all_flags[0].record_id == write_resp.record_id
