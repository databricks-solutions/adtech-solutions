"""Create tables and seed demo campaign budgets on app startup."""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import ProgrammingError

from .core.db import engine
from .models import Base, CampaignPacing

logger = logging.getLogger(__name__)

DEMO_CAMPAIGNS = [
    {"campaign_name": "Happy Dogs",      "budget_imps": 6_000_000, "cpm_rate":  8.00, "budget_dollars": 48000.00},
    {"campaign_name": "Terrific Tacos",  "budget_imps": 3_000_000, "cpm_rate": 12.00, "budget_dollars": 36000.00},
    {"campaign_name": "Best Burgers",    "budget_imps": 3_600_000, "cpm_rate": 10.00, "budget_dollars": 36000.00},
    {"campaign_name": "Cool Car",        "budget_imps": 2_000_000, "cpm_rate": 15.00, "budget_dollars": 30000.00},
    {"campaign_name": "Super Savings",   "budget_imps": 1_200_000, "cpm_rate": 10.00, "budget_dollars": 12000.00},
    {"campaign_name": "Fresh Flowers",   "budget_imps": 1_200_000, "cpm_rate":  7.00, "budget_dollars":  8400.00},
    {"campaign_name": "Moving Movie",    "budget_imps": 2_000_000, "cpm_rate": 12.00, "budget_dollars": 24000.00},
]


def init_db() -> None:
    """Create all tables defined in the ORM if they don't exist.

    If the app's service principal lacks CREATE permission (table was created
    by the lakebase_setup notebook with higher privileges), this logs a
    warning and continues — the table should already exist.
    """
    if inspect(engine).has_table("campaign_pacing"):
        logger.info("Table 'campaign_pacing' already exists — skipping DDL.")
        return
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created.")
    except ProgrammingError as exc:
        if "InsufficientPrivilege" in str(exc):
            logger.warning(
                "No CREATE permission on schema — table must be pre-created "
                "(run lakebase_setup notebook or grant CREATE to the app SP)."
            )
        else:
            raise


def seed_campaigns() -> None:
    """Insert demo campaigns if they don't already exist (won't overwrite impression counts)."""
    with engine.begin() as conn:
        for campaign in DEMO_CAMPAIGNS:
            stmt = (
                insert(CampaignPacing)
                .values(impression_count=0, **campaign)
                .on_conflict_do_nothing(index_elements=["campaign_name"])
            )
            conn.execute(stmt)
    logger.info("Seeded %d demo campaigns.", len(DEMO_CAMPAIGNS))
