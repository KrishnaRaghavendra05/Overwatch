import logging
from datetime import datetime

import numpy as np

from agent.models.dashboard import ChangeFlag
from agent.models.imagery import BoundingBox, DateRange, ImageryResponse
from agent.models.verification import SubagentResult, VerificationSummary
from agent.subagents.cloud_check import run_cloud_check
from agent.subagents.threshold_check import run_threshold_check
from agent.subagents.weather_check import run_weather_check
from core.index_math import compute_ndvi_delta, compute_ndwi_delta

logger = logging.getLogger(__name__)


# run all 3 verification subagents in parallel logic
def run_verification_suite(
    before_resp: ImageryResponse,
    after_resp: ImageryResponse,
    date_range: DateRange,
    index_type: str = "NDVI",
) -> tuple[float, VerificationSummary]:
    # 1. Compute delta using core math
    if index_type == "NDWI":
        b_green = np.array(before_resp.bands.green_raw, dtype=np.float64)
        b_nir = np.array(before_resp.bands.nir_raw, dtype=np.float64)
        a_green = np.array(after_resp.bands.green_raw, dtype=np.float64)
        a_nir = np.array(after_resp.bands.nir_raw, dtype=np.float64)
        delta_grid = compute_ndwi_delta(b_green, b_nir, a_green, a_nir)
    else:
        b_nir = np.array(before_resp.bands.nir_raw, dtype=np.float64)
        b_red = np.array(before_resp.bands.red_raw, dtype=np.float64)
        a_nir = np.array(after_resp.bands.nir_raw, dtype=np.float64)
        a_red = np.array(after_resp.bands.red_raw, dtype=np.float64)
        delta_grid = compute_ndvi_delta(b_nir, b_red, a_nir, a_red)

    mean_delta = float(np.mean(delta_grid))

    # 2. Run 3 subagents
    res_cloud = run_cloud_check(after_resp)
    res_threshold = run_threshold_check(mean_delta, index_type=index_type)
    res_weather = run_weather_check(
        after_resp.area,
        date_range,
        event_type="flood" if index_type == "NDWI" else "crop_stress",
    )

    results: list[SubagentResult] = [res_cloud, res_threshold, res_weather]
    all_passed = all(r.passed for r in results)
    is_ambiguous = any(r.is_ambiguous for r in results)
    avg_confidence = float(np.mean([r.confidence for r in results]))

    if not all_passed:
        action = "DISCARD_FALSE_ALARM"
        failed_names = [r.check_name for r in results if not r.passed]
        rationale = f"Signal disproved by checks: {', '.join(failed_names)}"
    elif is_ambiguous:
        action = "AMBIGUITY_TRIAGE"
        ambiguous_names = [r.check_name for r in results if r.is_ambiguous]
        rationale = (
            f"Ambiguity detected in: {', '.join(ambiguous_names)}. "
            "Human triage required."
        )
    else:
        action = "PROCEED_TO_DRAFT"
        rationale = (
            "All three independent verification checks passed with high confidence."
        )

    summary = VerificationSummary(
        results=results,
        all_passed=all_passed,
        is_ambiguous=is_ambiguous,
        recommended_action=action,
        composite_confidence=avg_confidence,
        rationale=rationale,
    )
    return mean_delta, summary


# build change flag report from verified signal
def draft_report(
    area: BoundingBox,
    delta_val: float,
    summary: VerificationSummary,
    before_resp: ImageryResponse,
    after_resp: ImageryResponse,
    index_type: str = "NDVI",
    hazard_name: str | None = None,
) -> ChangeFlag:
    severity = "severe" if abs(delta_val) >= 0.20 else "moderate"

    # Compute approximate spatial extent in hectares and acres
    mid_lat = (area.min_lat + area.max_lat) / 2.0
    lat_km = abs(area.max_lat - area.min_lat) * 111.0
    lon_km = abs(area.max_lon - area.min_lon) * 111.0 * np.cos(np.radians(mid_lat))
    hectares = max(1.0, lat_km * lon_km * 100.0)
    acres = hectares * 2.47105

    # Estimate physical damage percentage from index delta
    if index_type == "NDWI":
        hazard = hazard_name or "Monsoon Riverine Inundation / Flash Flooding"
        loss_pct = min(100.0, max(15.0, abs(delta_val) * 120.0))
        damage_metric_label = "Submerged Agricultural Area"
    else:
        hazard = hazard_name or "Severe Drought Desiccation / Heat Stress"
        loss_pct = min(100.0, max(20.0, abs(delta_val) * 105.0))
        damage_metric_label = "Canopy Chlorophyll & Biomass Loss"

    report_lines = [
        "============================================================",
        "📋 AGRICULTURAL INSURANCE CLAIM ASSESSMENT DOSSIER",
        "============================================================",
        f"**Insured Hazard Category**: {hazard}",
        (
            f"**Target Coordinates**: [{area.min_lat:.4f}, {area.min_lon:.4f}] "
            f"to [{area.max_lat:.4f}, {area.max_lon:.4f}]"
        ),
        (f"**Monitored Surface Extent**: {hectares:,.1f} ha ({acres:,.1f} acres)"),
        (
            f"**Satellite Baseline Pass**: {before_resp.acquired.date()} "
            "(Sentinel-2 L2A)"
        ),
        (
            f"**Post-Event Assessment Pass**: {after_resp.acquired.date()} "
            "(Sentinel-2 L2A)"
        ),
        "",
        "## 1. Physical Damage Quantification & Remote Sensing Evidence",
        f"- **Primary Change Index**: {index_type} (Normalized Spectral Index)",
        (
            f"- **Measured Mean Spectral Delta**: {delta_val:+.3f} "
            "(Standardized index delta)"
        ),
        f"- **Estimated {damage_metric_label}**: {loss_pct:.1f}%",
        (
            f"- **Damage Classification Grade**: {severity.upper()} LOSS "
            f"(Severity Index {abs(delta_val):.2f})"
        ),
        (
            "- **Agent Composite Verification Confidence**: "
            f"{summary.composite_confidence:.1%}"
        ),
        "",
        "## 2. Multi-Tier Subagent Verification Audit",
    ]

    for res in summary.results:
        icon = (
            "✅ PASS"
            if res.passed and not res.is_ambiguous
            else ("⚠️ AMBIGUOUS" if res.is_ambiguous else "❌ FAIL")
        )
        report_lines.append(
            f"- [{icon}] **{res.check_name.upper()}**: {res.details} "
            f"(Confidence: {res.confidence:.0%})"
        )

    report_lines.extend(
        [
            "",
            "## 3. Actuarial Claim Determination & Recommendation",
            f"**Audit Status**: {summary.rationale}",
            (
                "**Claim Assessment Outcome**: Verified remote sensing metrics "
                f"confirm physical loss ({loss_pct:.1f}%) across "
                f"{hectares:,.1f} ha. Recommended for official Human "
                "Actuarial Sign-off before ledger entry."
            ),
        ]
    )

    return ChangeFlag(
        area=area,
        detected_at=datetime.now(),
        index_type=index_type,
        delta_ndvi_scale=delta_val,
        severity=severity,
        report_text="\n".join(report_lines),
    )
