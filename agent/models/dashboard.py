from datetime import datetime

from pydantic import BaseModel

from agent.models.imagery import BoundingBox


# a detected change flag ready for review
class ChangeFlag(BaseModel):
    area: BoundingBox
    detected_at: datetime
    index_type: str  # "NDVI" or "NDWI"
    delta_ndvi_scale: float  # native -2..2 range, NOT percentage
    severity: str  # "moderate" or "severe"
    report_text: str  # human-readable draft for approval review


# payload sent to dashboard on approved write or retraction
class DashboardWritePayload(BaseModel):
    flag: ChangeFlag
    approved_by: str
    approved_at: datetime
    action: str  # "file" or "retract"


# what dashboard returns after a write or read-back
class DashboardReadResponse(BaseModel):
    record_id: str
    status: str  # "FILED", "RETRACTED", "PENDING"
    written_at: datetime
    area: BoundingBox
    verified: bool  # True if read-back matches write payload
    flag: ChangeFlag | None = None
