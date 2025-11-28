"""SEC document extraction service using LLM."""
from app.core.llm import LLMResponse, llm_client
from app.services.sec_client import sec_client

SCHEMAS = {
    "competitors": {
        "competitors": [
            {
                "name": "string - company name",
                "categories": ["string - GPU, CPU, Cloud, Networking, Automotive, or SoC"],
            }
        ],
        "competitive_factors": ["string - key competitive factors mentioned"],
    },
    "cybersecurity": {
        "frameworks": ["string - security frameworks mentioned"],
        "has_cso": "boolean",
        "cso_reports_to": "string or null",
        "cso_experience_years": "integer or null",
        "board_oversight": "string - which committee oversees cybersecurity",
        "has_incident_response_team": "boolean",
        "has_vendor_risk_process": "boolean",
        "key_practices": ["string - key cybersecurity practices mentioned"],
    },
    "risk_summary": {
        "risk_categories": ["string - high-level categories"],
        "risks": [{"title": "string - brief risk title", "category": "string - which category"}],
    },
    "business_overview": {
        "company_description": "string - one sentence description",
        "business_segments": [{"name": "string", "description": "string - brief description"}],
        "markets": ["string - market names"],
        "employee_count": "integer or null",
        "headquarters": "string",
        "key_technologies": ["string - core technologies mentioned"],
    },
}


class ExtractionService:
    def extract_competitors(self, ticker: str) -> tuple[dict | None, LLMResponse | None, str | None]:
        """Extract competitor information from 10-K."""
        html = sec_client.get_filing_html(ticker, "10-K")
        if not html:
            return None, None, f"Could not fetch 10-K for {ticker}"

        sections = sec_client.extract_10k_sections(html)
        competition_text = sections.get("competition")
        if not competition_text:
            return None, None, "Competition section not found in 10-K"

        result, response = llm_client.extract_json(
            text=competition_text,
            schema=SCHEMAS["competitors"],
            instructions="Extract competitors and competitive factors from this Competition section of an SEC 10-K filing.",
            metadata={"ticker": ticker, "section": "competition"},
        )
        return result, response, None

    def extract_cybersecurity(self, ticker: str) -> tuple[dict | None, LLMResponse | None, str | None]:
        """Extract cybersecurity governance info from 10-K."""
        html = sec_client.get_filing_html(ticker, "10-K")
        if not html:
            return None, None, f"Could not fetch 10-K for {ticker}"

        sections = sec_client.extract_10k_sections(html)
        cyber_text = sections.get("cybersecurity")
        if not cyber_text:
            return None, None, "Cybersecurity section not found in 10-K"

        result, response = llm_client.extract_json(
            text=cyber_text,
            schema=SCHEMAS["cybersecurity"],
            instructions="Extract cybersecurity governance and risk management information from this SEC 10-K filing section.",
            metadata={"ticker": ticker, "section": "cybersecurity"},
        )
        return result, response, None

    def extract_risks(self, ticker: str) -> tuple[dict | None, LLMResponse | None, str | None]:
        """Extract risk summary from 10-K."""
        html = sec_client.get_filing_html(ticker, "10-K")
        if not html:
            return None, None, f"Could not fetch 10-K for {ticker}"

        sections = sec_client.extract_10k_sections(html)
        risk_text = sections.get("risk_factors")
        if not risk_text:
            return None, None, "Risk factors section not found in 10-K"

        # Use only first 15K chars to reduce cost
        risk_text = risk_text[:15000]

        result, response = llm_client.extract_json(
            text=risk_text,
            schema=SCHEMAS["risk_summary"],
            instructions="Extract the risk categories and individual risks from this Risk Factors section of an SEC 10-K filing.",
            metadata={"ticker": ticker, "section": "risk_factors"},
        )
        return result, response, None

    def extract_business_overview(self, ticker: str) -> tuple[dict | None, LLMResponse | None, str | None]:
        """Extract business overview from 10-K."""
        html = sec_client.get_filing_html(ticker, "10-K")
        if not html:
            return None, None, f"Could not fetch 10-K for {ticker}"

        sections = sec_client.extract_10k_sections(html)
        business_text = sections.get("business")
        if not business_text:
            return None, None, "Business section not found in 10-K"

        # Use only first 8K chars
        business_text = business_text[:8000]

        result, response = llm_client.extract_json(
            text=business_text,
            schema=SCHEMAS["business_overview"],
            instructions="Extract business overview information from this SEC 10-K Business section.",
            metadata={"ticker": ticker, "section": "business"},
        )
        return result, response, None


extraction_service = ExtractionService()
