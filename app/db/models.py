"""SQLAlchemy models for SEC tracker database."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


class Company(Base):
    """Company information from SEC."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, index=True, nullable=False)
    cik = Column(String(10), index=True)
    name = Column(String(255))
    sic = Column(String(10))
    sic_description = Column(String(255))
    fiscal_year_end = Column(String(10))
    state_of_incorporation = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ai_extractions = relationship("AIExtraction", back_populates="company")


class AIExtraction(Base):
    """AI deep-dive extraction from a 10-K filing."""

    __tablename__ = "ai_extractions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # Filing metadata
    filing_date = Column(Date, nullable=False)
    fiscal_year = Column(String(4), nullable=False)

    # Core AI analysis
    ai_narrative_stance = Column(
        String(50), nullable=False
    )  # opportunity-focused, risk-focused, balanced, minimal
    ai_mention_count = Column(Integer, default=0)

    # AI products and services (JSONB array)
    # Each item: {name, description, monetization}
    ai_products_services = Column(JSONB, default=list)

    # AI risks disclosed (JSONB array)
    # Each item: {risk, category}
    ai_risks_disclosed = Column(JSONB, default=list)

    # Investment signals
    infrastructure_mentions = Column(Text)
    partnerships = Column(ARRAY(String), default=list)
    acquisitions = Column(ARRAY(String), default=list)

    # Competitive position
    claimed_advantages = Column(ARRAY(String), default=list)
    named_competitors = Column(ARRAY(String), default=list)
    market_position_claim = Column(Text)

    # Metrics
    revenue_mentions = Column(Text)
    adoption_metrics = Column(Text)
    other_kpis = Column(ARRAY(String), default=list)

    # Key quotes
    key_ai_quotes = Column(ARRAY(String), default=list)

    # LLM metadata
    llm_model = Column(String(100))
    llm_cost_usd = Column(Float)
    llm_tokens = Column(Integer)

    # Timestamps
    extracted_at = Column(DateTime, default=datetime.utcnow)

    # Ensure one extraction per company per fiscal year
    __table_args__ = (
        UniqueConstraint("company_id", "fiscal_year", name="uix_company_fiscal_year"),
    )

    # Relationships
    company = relationship("Company", back_populates="ai_extractions")

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "ticker": self.company.ticker if self.company else None,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "fiscal_year": self.fiscal_year,
            "ai_narrative_stance": self.ai_narrative_stance,
            "ai_mention_count": self.ai_mention_count,
            "ai_products_services": self.ai_products_services or [],
            "ai_risks_disclosed": self.ai_risks_disclosed or [],
            "ai_investments": {
                "infrastructure_mentions": self.infrastructure_mentions,
                "partnerships": self.partnerships or [],
                "acquisitions": self.acquisitions or [],
            },
            "ai_competitive_position": {
                "claimed_advantages": self.claimed_advantages or [],
                "named_competitors": self.named_competitors or [],
                "market_position_claim": self.market_position_claim,
            },
            "ai_metrics": {
                "revenue_mentions": self.revenue_mentions,
                "adoption_metrics": self.adoption_metrics,
                "other_kpis": self.other_kpis or [],
            },
            "key_ai_quotes": self.key_ai_quotes or [],
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
        }
