"""FastAPI routes for SEC data extraction."""
from fastapi import APIRouter, HTTPException

from app.core.llm import llm_client
from app.models.schemas import (
    BusinessOverviewResponse,
    CompanyInfo,
    CompetitorResponse,
    CybersecurityResponse,
    RiskResponse,
    SessionStats,
)
from app.services.extraction import extraction_service
from app.services.sec_client import sec_client

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
