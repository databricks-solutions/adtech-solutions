from sqlalchemy import BigInteger, Column, DateTime, Numeric, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class CampaignPacing(Base):
    __tablename__ = "campaign_pacing"

    campaign_name = Column(String(100), primary_key=True)
    impression_count = Column(BigInteger, nullable=False, default=0)
    budget_imps = Column(BigInteger, nullable=False)
    cpm_rate = Column(Numeric(8, 2), nullable=False)
    budget_dollars = Column(Numeric(10, 2), nullable=False)
    last_updated = Column(DateTime(timezone=True))
