from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models import CampaignPacing
from ..seed import DEMO_CAMPAIGNS

router = APIRouter()


class CampaignResponse(BaseModel):
    campaign_name: str
    impression_count: int
    budget_imps: int
    budget_dollars: float
    spend_dollars: float
    pacing_pct: float
    status: Literal["ACTIVE", "PACING_FAST", "STOPPED"]
    last_updated: datetime | None


def _compute_status(pacing_pct: float) -> Literal["ACTIVE", "PACING_FAST", "STOPPED"]:
    if pacing_pct >= 100.0:
        return "STOPPED"
    if pacing_pct >= 80.0:
        return "PACING_FAST"
    return "ACTIVE"


@router.get("/campaigns", response_model=list[CampaignResponse])
def get_campaigns(db: Session = Depends(get_db)) -> list[CampaignResponse]:
    """
    Return all campaigns with computed spend, pacing %, and status.
    Sorted by pacing_pct descending (most at-risk on top).
    """
    rows = db.query(CampaignPacing).all()
    results: list[CampaignResponse] = []

    for row in rows:
        imps = int(row.impression_count or 0)
        budget_imps = int(row.budget_imps or 1)
        cpm = float(row.cpm_rate or 0)
        budget_dollars = float(row.budget_dollars or 0)

        spend = round(imps / 1000.0 * cpm, 2)
        pacing_pct = round(imps / budget_imps * 100.0, 1)

        # Normalize last_updated to UTC-aware datetime
        last_updated = row.last_updated
        if last_updated and last_updated.tzinfo is None:
            last_updated = last_updated.replace(tzinfo=timezone.utc)

        results.append(
            CampaignResponse(
                campaign_name=row.campaign_name,
                impression_count=imps,
                budget_imps=budget_imps,
                budget_dollars=budget_dollars,
                spend_dollars=spend,
                pacing_pct=pacing_pct,
                status=_compute_status(pacing_pct),
                last_updated=last_updated,
            )
        )

    return sorted(results, key=lambda r: r.pacing_pct, reverse=True)


@router.post("/campaigns/reset")
def reset_campaigns(db: Session = Depends(get_db)):
    """Reset all campaigns to zero impressions and re-seed budget values."""
    db.query(CampaignPacing).delete()
    for campaign in DEMO_CAMPAIGNS:
        db.add(CampaignPacing(impression_count=0, **campaign))
    db.commit()
    return {"status": "ok", "message": "All campaigns reset to zero."}
