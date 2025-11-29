"""FastAPI routes for SEC data extraction."""
from fastapi import APIRouter, HTTPException

from app.core.llm import llm_client
from app.models.schemas import (
    AIExtractionResponse,
    AIHistoryResponse,
    AIHistoryTrend,
    AIYearData,
    BusinessOverviewResponse,
    CompanyInfo,
    CompanySearchResponse,
    CompanySearchResult,
    CompetitorResponse,
    CybersecurityResponse,
    RiskResponse,
    SessionStats,
    TickerLookupResult,
)
from app.services.extraction import extraction_service
from app.services.sec_client import sec_client
from app.services.ticker_lookup import ticker_lookup

router = APIRouter()


def _llm_response_to_metrics(response) -> dict | None:
    if not response:
        return None
    return {
        "request_id": response.request_id,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "total_tokens": response.total_tokens,
        "cost_usd": response.cost_usd,
        "latency_ms": response.latency_ms,
    }


@router.get("/search", response_model=CompanySearchResponse)
async def search_companies(q: str, limit: int = 10):
    """
    Search for companies by name, brand, or subsidiary.

    Uses multi-stage lookup:
    1. Direct fuzzy match against SEC company names
    2. Wikidata lookup for subsidiaries (e.g., "WhatsApp" → META)
    3. LLM fallback for typos and brand aliases

    Returns list of matches with confidence scores and lookup method.
    """
    results = ticker_lookup.search(q, limit=min(limit, 50))
    return CompanySearchResponse(
        query=q,
        results=[CompanySearchResult(**r) for r in results],
    )


@router.get("/lookup", response_model=TickerLookupResult)
async def lookup_ticker(q: str):
    """
    Resolve a company name/brand/subsidiary to a single SEC ticker.

    Best for when you need one definitive answer rather than a list.
    Uses the same multi-stage lookup as /search but returns only the best match.
    """
    result = ticker_lookup.lookup(q)
    return TickerLookupResult(
        query=result.query,
        ticker=result.ticker,
        company_name=result.company_name,
        method=result.method.value,
        confidence=result.confidence,
        chain=result.chain,
    )


@router.get("/company/{ticker}", response_model=CompanyInfo)
async def get_company_info(ticker: str):
    """Get basic company information from SEC."""
    info = sec_client.get_company_info(ticker)
    if not info:
        raise HTTPException(status_code=404, detail=f"Company not found: {ticker}")

    return CompanyInfo(
        cik=info["cik"],
        name=info["name"],
        ticker=info["tickers"][0] if info["tickers"] else ticker.upper(),
        sic=info["sic"],
        sic_description=info["sicDescription"],
        fiscal_year_end=info["fiscalYearEnd"],
        state_of_incorporation=info["stateOfIncorporation"],
        recent_filings_count=len(info["filings"]["recent"]["form"]),
    )


@router.get("/extract/{ticker}/competitors", response_model=CompetitorResponse)
async def extract_competitors(ticker: str):
    """Extract competitor information from company's 10-K."""
    data, response, error = extraction_service.extract_competitors(ticker)
    return CompetitorResponse(
        ticker=ticker.upper(),
        data=data,
        llm_metrics=_llm_response_to_metrics(response),
        error=error or (response.error if response else None),
    )


@router.get("/extract/{ticker}/cybersecurity", response_model=CybersecurityResponse)
async def extract_cybersecurity(ticker: str):
    """Extract cybersecurity governance info from company's 10-K."""
    data, response, error = extraction_service.extract_cybersecurity(ticker)
    return CybersecurityResponse(
        ticker=ticker.upper(),
        data=data,
        llm_metrics=_llm_response_to_metrics(response),
        error=error or (response.error if response else None),
    )


@router.get("/extract/{ticker}/risks", response_model=RiskResponse)
async def extract_risks(ticker: str):
    """Extract risk summary from company's 10-K."""
    data, response, error = extraction_service.extract_risks(ticker)
    return RiskResponse(
        ticker=ticker.upper(),
        data=data,
        llm_metrics=_llm_response_to_metrics(response),
        error=error or (response.error if response else None),
    )


@router.get("/extract/{ticker}/business", response_model=BusinessOverviewResponse)
async def extract_business_overview(ticker: str):
    """Extract business overview from company's 10-K."""
    data, response, error = extraction_service.extract_business_overview(ticker)
    return BusinessOverviewResponse(
        ticker=ticker.upper(),
        data=data,
        llm_metrics=_llm_response_to_metrics(response),
        error=error or (response.error if response else None),
    )


@router.get("/extract/{ticker}/ai", response_model=AIExtractionResponse)
async def extract_ai_deep_dive(ticker: str):
    """
    Extract AI-focused analysis from company's 10-K.

    Analyzes the company's AI narrative, products, risks, investments,
    competitive position, and key metrics. Useful for tracking how
    companies are positioning themselves in the AI landscape.

    Returns:
        - ai_narrative_stance: opportunity-focused, risk-focused, balanced, or minimal
        - ai_mention_count: Total AI-related term mentions in filing
        - ai_products_services: Named AI products and monetization
        - ai_risks_disclosed: AI-specific risks with categories
        - ai_investments: Infrastructure, partnerships, acquisitions
        - ai_competitive_position: Claimed advantages and named competitors
        - ai_metrics: Revenue, adoption, and other KPIs
        - key_ai_quotes: Most significant AI strategy statements
    """
    data, response, error, filing_info = extraction_service.extract_ai_deep_dive(ticker)
    return AIExtractionResponse(
        ticker=ticker.upper(),
        filing_date=filing_info.get("filing_date") if filing_info else None,
        fiscal_year=filing_info.get("fiscal_year") if filing_info else None,
        data=data,
        llm_metrics=_llm_response_to_metrics(response),
        error=error or (response.error if response else None),
    )


@router.get("/extract/{ticker}/ai/history", response_model=AIHistoryResponse)
async def extract_ai_history(ticker: str, years: int = 5):
    """
    Extract AI-focused analysis from multiple years of 10-K filings.

    Analyzes the company's AI narrative evolution over time, enabling
    trend analysis of how companies have adapted to AI.

    Args:
        ticker: Company ticker symbol
        years: Number of years to analyze (default 5, max 10)

    Returns:
        - years: List of AI extractions per fiscal year
        - trend_summary: Aggregated trends including:
            - ai_mention_counts: Year-over-year mention counts
            - stance_changes: How AI narrative stance evolved
            - total_cost_usd: Total LLM cost for all extractions
    """
    years = min(years, 10)  # Cap at 10 years

    results, error = extraction_service.extract_ai_history(ticker, years=years)

    if error and not results:
        return AIHistoryResponse(
            ticker=ticker.upper(),
            years_requested=years,
            years_found=0,
            years=[],
            trend_summary=None,
            error=error,
        )

    # Convert results to response format
    year_data = []
    ai_mention_counts = {}
    stance_changes = []
    total_cost = 0.0
    total_latency = 0.0

    for r in results:
        llm_metrics = None
        if r.llm_response:
            llm_metrics = _llm_response_to_metrics(r.llm_response)
            total_cost += r.llm_response.cost_usd
            total_latency += r.llm_response.latency_ms

        year_data.append(AIYearData(
            fiscal_year=r.fiscal_year,
            filing_date=r.filing_date,
            data=r.data,
            llm_metrics=llm_metrics,
            error=r.error,
        ))

        # Track trends
        if r.data:
            ai_mention_counts[r.fiscal_year] = r.data.get("ai_mention_count", 0)
            stance_changes.append({
                "year": r.fiscal_year,
                "stance": r.data.get("ai_narrative_stance", "unknown"),
            })

    # Sort stance_changes by year ascending for cleaner trend view
    stance_changes.sort(key=lambda x: x["year"])

    trend_summary = AIHistoryTrend(
        ai_mention_counts=ai_mention_counts,
        stance_changes=stance_changes,
        total_cost_usd=total_cost,
        total_latency_ms=total_latency,
    )

    return AIHistoryResponse(
        ticker=ticker.upper(),
        years_requested=years,
        years_found=len(results),
        years=year_data,
        trend_summary=trend_summary,
        error=None,
    )


@router.get("/llm/stats", response_model=SessionStats)
async def get_llm_stats():
    """Get LLM usage statistics for current session."""
    stats = llm_client.get_session_stats()
    if stats["total_requests"] == 0:
        return SessionStats(
            total_requests=0,
            total_tokens=0,
            input_tokens=0,
            output_tokens=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            errors=0,
        )
    return SessionStats(**stats)


@router.get("/llm/log")
async def get_llm_log():
    """Get full LLM request log for current session."""
    return llm_client.get_request_log()


@router.post("/llm/clear")
async def clear_llm_log():
    """Clear the LLM request log."""
    llm_client.clear_log()
    return {"status": "cleared"}
