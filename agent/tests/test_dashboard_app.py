from fastapi.testclient import TestClient

from dashboard.app import app
from scripts.seed_sample_data import seed

client = TestClient(app)


def setup_module() -> None:
    seed(42)


def test_dashboard_index_html() -> None:
    """Dashboard root renders HTML with active claims and scenarios."""
    response = client.get("/")
    assert response.status_code == 200
    assert "OVERWATCH" in response.text
    assert "leaflet" in response.text


def test_dashboard_flags_api() -> None:
    """Flags JSON endpoint returns list of records."""
    response = client.get("/flags")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_dashboard_api_agent_run_and_decision() -> None:
    """TrueForge agent run endpoint pauses at Approval Gate and files on decision."""
    # 1. Run agent pipeline up to Human Approval Gate
    run_resp = client.post("/api/agent/run", json={"scenario_key": "crop_damage"})
    assert run_resp.status_code == 200
    data = run_resp.json()
    assert data["gate_required"] == "APPROVAL_GATE"
    assert "session_id" in data
    assert data["step_2_mcp"]["tool"] == "mcp://overwatch-imagery/fetch_imagery"

    # 2. Submit Human Approval Decision
    dec_resp = client.post(
        "/api/agent/decision",
        json={
            "session_id": data["session_id"],
            "decision": "APPROVE",
            "approver": "Test Approver",
        },
    )
    assert dec_resp.status_code == 200
    dec_data = dec_resp.json()
    assert dec_data["status"] == "VERIFIED_FILED"
    assert "record_id" in dec_data
