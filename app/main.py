"""FastAPI application for SEC data extraction."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="SEC Tracker API",
    description="Extract structured data from SEC EDGAR filings using LLM",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "SEC Tracker API",
        "version": "0.1.0",
        "endpoints": {
            "company_info": "/api/company/{ticker}",
            "extract_competitors": "/api/extract/{ticker}/competitors",
            "extract_cybersecurity": "/api/extract/{ticker}/cybersecurity",
            "extract_risks": "/api/extract/{ticker}/risks",
            "extract_business": "/api/extract/{ticker}/business",
            "llm_stats": "/api/llm/stats",
            "llm_log": "/api/llm/log",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
