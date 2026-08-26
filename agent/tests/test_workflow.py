from datetime import date

from agent.models.imagery import BoundingBox, DateRange
from agent.services.cache import get_or_fetch
from agent.workflow.ambiguity_gate import TriageDecision, handle_ambiguity_triage
from agent.workflow.approval_gate import (
    execute_approved_write,
    present_and_await_approval,
)
from agent.workflow.draft_report import draft_report, run_verification_suite
from agent.workflow.retraction import execute_approved_retraction, propose_retraction
from dashboard.read import read_flag
from scripts.seed_sample_data import seed


def setup_module() -> None:
    # Ensure cached sample datasets are seeded before tests run
    seed(42)


def test_scenario_1_crop_damage_end_to_end() -> None:
    """Scenario 1: True positive crop damage passes all 3 subagents and writes to DB."""
    area = BoundingBox(min_lon=-93.55, min_lat=42.01, max_lon=-93.50, max_lat=42.05)
    d_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    d_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))

    before_resp = get_or_fetch(area, d_before)
    after_resp = get_or_fetch(area, d_after)

    # 1. Run 3 subagents
    mean_delta, summary = run_verification_suite(before_resp, after_resp, d_after)
    assert summary.all_passed is True
    assert summary.is_ambiguous is False
    assert summary.recommended_action == "PROCEED_TO_DRAFT"
    assert mean_delta < -0.20

    # 2. Draft report
    flag = draft_report(area, mean_delta, summary, before_resp, after_resp)
    assert flag.severity == "severe"

    # 3. Human Approval Gate
    approved = present_and_await_approval(flag, interactive=False)
    assert approved is True

    # 4. Write & Read-back Verification
    write_resp = execute_approved_write(flag, approver="Kaamil Hifzaan")
    assert write_resp.verified is True
    assert write_resp.status == "FILED"

    # Read back directly to verify state
    db_record = read_flag(write_resp.record_id)
    assert db_record is not None
    assert db_record.status == "FILED"


def test_scenario_2_cloud_false_positive_rejected() -> None:
    """Scenario 2: Cloud shadow artifact is rejected by Cloud Subagent."""
    area = BoundingBox(min_lon=-62.10, min_lat=-3.45, max_lon=-62.05, max_lat=-3.40)
    d_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    d_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))

    before_resp = get_or_fetch(area, d_before)
    after_resp = get_or_fetch(area, d_after)

    _, summary = run_verification_suite(before_resp, after_resp, d_after)
    assert summary.all_passed is False
    assert summary.recommended_action == "DISCARD_FALSE_ALARM"


def test_scenario_3_ambiguity_triage_flow() -> None:
    """Scenario 3: Thin haze triggers Ambiguity Triage Gate."""
    area = BoundingBox(min_lon=-119.80, min_lat=36.70, max_lon=-119.75, max_lat=36.75)
    d_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    d_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))

    before_resp = get_or_fetch(area, d_before)
    after_resp = get_or_fetch(area, d_after)

    _, summary = run_verification_suite(before_resp, after_resp, d_after)
    assert summary.is_ambiguous is True
    assert summary.recommended_action == "AMBIGUITY_TRIAGE"

    # Human handles triage
    decision = handle_ambiguity_triage(
        summary,
        default_choice=TriageDecision.ACCEPT_AS_DAMAGE,
        interactive=False,
    )
    assert decision == TriageDecision.ACCEPT_AS_DAMAGE


def test_retraction_lifecycle() -> None:
    """Scenario: Previously filed record is retracted via human gate."""
    area = BoundingBox(min_lon=-93.55, min_lat=42.01, max_lon=-93.50, max_lat=42.05)
    d_before = DateRange(start=date(2026, 6, 1), end=date(2026, 6, 2))
    d_after = DateRange(start=date(2026, 7, 15), end=date(2026, 7, 16))

    before_resp = get_or_fetch(area, d_before)
    after_resp = get_or_fetch(area, d_after)
    mean_delta, summary = run_verification_suite(before_resp, after_resp, d_after)
    flag = draft_report(area, mean_delta, summary, before_resp, after_resp)

    # File first
    write_resp = execute_approved_write(flag, approver="Kaamil Hifzaan")
    record_id = write_resp.record_id

    # Now propose and execute retraction
    propose_ok = propose_retraction(
        record_id,
        reason="Follow-up clean tile confirmed transient sensor artifact",
        interactive=False,
    )
    assert propose_ok is True

    retract_resp = execute_approved_retraction(record_id, approver="Kaamil Hifzaan")
    assert retract_resp.status == "RETRACTED"

    db_record = read_flag(record_id)
    assert db_record is not None
    assert db_record.status == "RETRACTED"
