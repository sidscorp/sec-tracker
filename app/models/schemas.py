"""Pydantic schemas for API responses."""
from pydantic import BaseModel


class LLMMetrics(BaseModel):
    request_id: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float


class Competitor(BaseModel):
    name: str
    categories: list[str]


class CompetitorExtraction(BaseModel):
    competitors: list[Competitor]
    competitive_factors: list[str]


class CompetitorResponse(BaseModel):
    ticker: str
    data: CompetitorExtraction | None
    llm_metrics: LLMMetrics | None
    error: str | None


class CybersecurityExtraction(BaseModel):
    frameworks: list[str]
    has_cso: bool
    cso_reports_to: str | None
    cso_experience_years: int | None
    board_oversight: str
    has_incident_response_team: bool
    has_vendor_risk_process: bool
    key_practices: list[str]


class CybersecurityResponse(BaseModel):
    ticker: str
    data: CybersecurityExtraction | None
    llm_metrics: LLMMetrics | None
    error: str | None


class Risk(BaseModel):
    title: str
    category: str


class RiskExtraction(BaseModel):
    risk_categories: list[str]
    risks: list[Risk]


class RiskResponse(BaseModel):
    ticker: str
    data: RiskExtraction | None
    llm_metrics: LLMMetrics | None
    error: str | None


class BusinessSegment(BaseModel):
    name: str
    description: str


class BusinessOverviewExtraction(BaseModel):
    company_description: str
    business_segments: list[BusinessSegment]
    markets: list[str]
    employee_count: int | None
    headquarters: str
    key_technologies: list[str]


class BusinessOverviewResponse(BaseModel):
    ticker: str
    data: BusinessOverviewExtraction | None
    llm_metrics: LLMMetrics | None
    error: str | None


class SessionStats(BaseModel):
    total_requests: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    errors: int


class CompanyInfo(BaseModel):
    cik: str
    name: str
    ticker: str
    sic: str
    sic_description: str
    fiscal_year_end: str
    state_of_incorporation: str
    recent_filings_count: int


class CompanySearchResult(BaseModel):
    """A single company search result."""
    ticker: str
    name: str
    cik: str | None
    match_type: str  # "direct", "wikidata", "llm", "fallback"
    score: float
    chain: list[str] | None = None  # Ownership chain for subsidiary matches


class CompanySearchResponse(BaseModel):
    """Response for company search endpoint."""
    query: str
    results: list[CompanySearchResult]


class TickerLookupResult(BaseModel):
    """Result of resolving a query to a single ticker."""
    query: str
    ticker: str | None
    company_name: str | None
    method: str  # "direct", "wikidata", "llm", "fallback"
    confidence: float
    chain: list[str] | None = None
