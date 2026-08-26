from datetime import datetime, timezone

import pytest

from agent.models.imagery import (
    BoundingBox,
    DateRange,
    ImageryResponse,
    SpectralBands,
)
from agent.subagents.cloud_check import run_cloud_check
from agent.subagents.threshold_check import run_threshold_check
from agent.subagents.weather_check import run_weather_check
from agent.workflow.approval_gate import (
    execute_approved_write,
    present_and_await_approval,
)
from agent.workflow.draft_report import draft_report
from agent.workflow.retraction import (
    execute_approved_retraction,
    propose_retraction,
)
from dashboard.db import init_db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_workflow.db"
    monkeypatch.setattr("dashboard.db.DASHBOARD_DB_PATH", test_db)
    monkeypatch.setattr("agent.config.DASHBOARD_DB_PATH", test_db)
    init_db()


def test_subagent_verifications():
    area = BoundingBox(min_lon=10.0, min_lat=20.0, max_lon=10.5, max_lat=20.5)
    img_resp_clean = ImageryResponse(
        request_id="test-clean",
        acquired=datetime.now(timezone.utc),
        area=area,
        bands=SpectralBands(
            nir_raw=[[0.8, 0.8]], red_raw=[[0.2, 0.2]], green_raw=[[0.3, 0.3]]
        ),
        cloud_cover_pct_0_100=5.0,
    )
    img_resp_cloudy = ImageryResponse(
        request_id="test-cloudy",
        acquired=datetime.now(timezone.utc),
        area=area,
        bands=SpectralBands(
            nir_raw=[[0.8, 0.8]], red_raw=[[0.2, 0.2]], green_raw=[[0.3, 0.3]]
        ),
        cloud_cover_pct_0_100=65.0,
    )

    assert run_cloud_check(img_resp_clean) is True
    assert run_cloud_check(img_resp_cloudy) is False

    assert run_threshold_check(-0.3) is True
    assert run_threshold_check(-0.02) is False

    dr = DateRange(start=datetime.now().date(), end=datetime.now().date())
    assert run_weather_check(area, dr) is True


def test_end_to_end_approval_and_retraction():
    area = BoundingBox(min_lon=10.0, min_lat=20.0, max_lon=10.5, max_lat=20.5)
    flag = draft_report(area=area, delta_ndvi_scale=-0.35, checks_passed=True)
    assert flag.severity == "severe"

    approved = present_and_await_approval(flag)
    assert approved is True

    write_resp = execute_approved_write(flag, approver="inspector_alice")
    assert write_resp.verified is True
    assert write_resp.status == "filed"

    # Retraction flow
    proposed = propose_retraction(write_resp.record_id, reason="seasonal shadow")
    assert proposed is True

    retract_resp = execute_approved_retraction(
        write_resp.record_id, approver="inspector_alice"
    )
    assert retract_resp.verified is True
    assert retract_resp.status == "retracted"
