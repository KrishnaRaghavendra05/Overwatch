from pydantic import BaseModel, Field


# result from an individual verification subagent
class SubagentResult(BaseModel):
    check_name: str  # "cloud_shadow", "threshold", "weather"
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    details: str
    is_ambiguous: bool = False
    metrics: dict[str, float | str | int | bool] = Field(default_factory=dict)


# composite summary across all three parallel subagents
class VerificationSummary(BaseModel):
    results: list[SubagentResult]
    # True if no subagent outright failed (ambiguous counts as passed)
    all_passed: bool
    # True if any subagent flagged ambiguity (split confidence)
    is_ambiguous: bool
    recommended_action: str
    # "PROCEED_TO_DRAFT", "AMBIGUITY_TRIAGE", "DISCARD_FALSE_ALARM"
    composite_confidence: float
    rationale: str
