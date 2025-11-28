"""SEC document extraction service using LLM."""
import re

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
    "ai_deep_dive": {
        "ai_narrative_stance": "string - 'opportunity-focused', 'risk-focused', 'balanced', or 'minimal'",
        "ai_products_services": [
            {
                "name": "string - product/service name",
                "description": "string - brief description",
                "monetization": "string or null - how they're making money from it",
            }
        ],
        "ai_risks_disclosed": [
            {
                "risk": "string - the risk",
                "category": "string - 'competition', 'regulation', 'talent', 'ethics', 'IP/legal', 'execution', 'dependency', or 'other'",
            }
        ],
        "ai_investments": {
            "infrastructure_mentions": "string or null - any CapEx/infrastructure mentions",
            "partnerships": ["string - named AI partnerships"],
            "acquisitions": ["string - AI-related acquisitions mentioned"],
        },
        "ai_competitive_position": {
            "claimed_advantages": ["string - what they claim as differentiation"],
            "named_competitors": ["string - companies named as AI competitors"],
            "market_position_claim": "string or null - how they describe their market position",
        },
        "ai_metrics": {
            "revenue_mentions": "string or null - any AI revenue figures or growth rates",
            "adoption_metrics": "string or null - customer/user adoption numbers",
            "other_kpis": ["string - other quantitative AI metrics"],
        },
        "key_ai_quotes": ["string - 2-3 most significant statements about AI strategy"],
    },
}

AI_EXTRACTION_INSTRUCTIONS = """Analyze this SEC 10-K filing for AI-related information.

Focus on extracting:
1. The company's overall stance on AI (are they positioning it as opportunity or risk?)
2. Specific AI products, services, and how they're monetizing them
3. AI-related risks they've disclosed (categorize each risk)
4. Investment signals (infrastructure spending, partnerships, acquisitions)
5. How they position themselves vs competitors in AI
6. Any quantitative metrics about AI impact (revenue, adoption, KPIs)
7. Key strategic quotes about their AI direction (2-3 most important)

Be specific and cite actual details from the filing. If AI is barely mentioned, set stance to 'minimal'.
For risk categories use: competition, regulation, talent, ethics, IP/legal, execution, dependency, or other."""


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

    def _count_ai_mentions(self, text: str) -> int:
        """Count AI-related term mentions in text."""
        patterns = [
            r"\bAI\b",
            r"\bartificial\s+intelligence\b",
            r"\bmachine\s+learning\b",
            r"\bdeep\s+learning\b",
            r"\bgenerative\s+AI\b",
            r"\bLLM\b",
            r"\blarge\s+language\s+model\b",
            r"\bneural\s+network\b",
        ]
        total = 0
        for pattern in patterns:
            total += len(re.findall(pattern, text, re.IGNORECASE))
        return total

    def extract_ai_deep_dive(
        self, ticker: str
    ) -> tuple[dict | None, LLMResponse | None, str | None, dict | None]:
        """
        Extract AI-focused information from 10-K.

        Returns:
            tuple of (result, llm_response, error, filing_info)
            filing_info contains filing_date and fiscal_year if available
        """
        # Get filing info for metadata
        company_info = sec_client.get_company_info(ticker)
        if not company_info:
            return None, None, f"Could not fetch company info for {ticker}", None

        # Find the most recent 10-K filing date
        filings = company_info["filings"]["recent"]
        filing_date = None
        fiscal_year = None
        for i, form in enumerate(filings["form"]):
            if form == "10-K":
                filing_date = filings["filingDate"][i]
                fiscal_year = filings["reportDate"][i][:4]  # Extract year
                break

        html = sec_client.get_filing_html(ticker, "10-K")
        if not html:
            return None, None, f"Could not fetch 10-K for {ticker}", None

        sections = sec_client.extract_10k_sections(html)
        full_text = sec_client._html_to_text(html)

        # Count AI mentions for metadata
        ai_mention_count = self._count_ai_mentions(full_text)

        # Combine relevant sections for comprehensive AI analysis
        combined_text = ""
        if sections.get("business"):
            combined_text += "=== BUSINESS SECTION ===\n" + sections["business"][:25000] + "\n\n"
        if sections.get("risk_factors"):
            combined_text += "=== RISK FACTORS ===\n" + sections["risk_factors"][:15000] + "\n\n"
        if sections.get("mdna"):
            combined_text += "=== MD&A ===\n" + sections["mdna"][:10000] + "\n\n"
        if sections.get("competition"):
            combined_text += "=== COMPETITION ===\n" + sections["competition"][:5000]

        if not combined_text:
            return None, None, "No sections found in 10-K", None

        result, response = llm_client.extract_json(
            text=combined_text,
            schema=SCHEMAS["ai_deep_dive"],
            instructions=AI_EXTRACTION_INSTRUCTIONS,
            metadata={"ticker": ticker, "analysis": "ai_deep_dive"},
        )

        # Add AI mention count to result
        if result:
            result["ai_mention_count"] = ai_mention_count

        filing_info = {
            "filing_date": filing_date,
            "fiscal_year": fiscal_year,
        }

        return result, response, None, filing_info


extraction_service = ExtractionService()
