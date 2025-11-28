"""SEC EDGAR API client."""
import re
from functools import lru_cache

import httpx

from app.core.config import settings

HEADERS = {"User-Agent": settings.SEC_USER_AGENT}
BASE_URL = "https://data.sec.gov"
SEC_URL = "https://www.sec.gov"


class SECClient:
    def __init__(self):
        self._http = httpx.Client(headers=HEADERS, timeout=60)
        self._ticker_map: dict[str, dict] | None = None

    def _get_ticker_map(self) -> dict[str, dict]:
        if self._ticker_map is None:
            url = f"{SEC_URL}/files/company_tickers.json"
            response = self._http.get(url)
            response.raise_for_status()
            data = response.json()
            self._ticker_map = {v["ticker"]: v for v in data.values()}
        return self._ticker_map

    def ticker_to_cik(self, ticker: str) -> str | None:
        ticker_map = self._get_ticker_map()
        info = ticker_map.get(ticker.upper())
        if info:
            return str(info["cik_str"]).zfill(10)
        return None

    def get_company_info(self, ticker: str) -> dict | None:
        cik = self.ticker_to_cik(ticker)
        if not cik:
            return None

        url = f"{BASE_URL}/submissions/CIK{cik}.json"
        response = self._http.get(url)
        response.raise_for_status()
        return response.json()

    def get_company_facts(self, ticker: str) -> dict | None:
        cik = self.ticker_to_cik(ticker)
        if not cik:
            return None

        url = f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        response = self._http.get(url)
        response.raise_for_status()
        return response.json()

    def get_filing_html(self, ticker: str, form_type: str = "10-K") -> str | None:
        """Get the HTML content of the most recent filing of given type."""
        info = self.get_company_info(ticker)
        if not info:
            return None

        cik = str(info["cik"]).lstrip("0")
        filings = info["filings"]["recent"]

        for i, form in enumerate(filings["form"]):
            if form == form_type:
                accession = filings["accessionNumber"][i].replace("-", "")
                primary_doc = filings["primaryDocument"][i]
                url = f"{SEC_URL}/Archives/edgar/data/{cik}/{accession}/{primary_doc}"
                response = self._http.get(url)
                response.raise_for_status()
                return response.text

        return None

    def extract_10k_sections(self, html: str) -> dict[str, str]:
        """Extract key sections from 10-K HTML."""
        html_clean = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html_clean = re.sub(r"<script[^>]*>.*?</script>", "", html_clean, flags=re.DOTALL | re.IGNORECASE)

        text = re.sub(r"<(?:p|div|br|tr|h[1-6])[^>]*>", "\n", html_clean, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        text = re.sub(r"&#\d+;", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        full_text = text.strip()

        sections = {}

        # Business section
        business_start = full_text.find("NVIDIA pioneered")
        if business_start == -1:
            business_match = re.search(r"Item\s*1\.?\s*Business.*?Our Company", full_text, re.IGNORECASE)
            if business_match:
                business_start = business_match.start()

        if business_start > 0:
            business_end = full_text.find("Item 1A", business_start + 100)
            if business_end > business_start:
                sections["business"] = full_text[business_start:business_end].strip()

        # Risk factors
        risk_start = full_text.find("Risk Factors Summary")
        if risk_start > 0:
            risk_end = full_text.find("Item 1B", risk_start + 100)
            if risk_end == -1:
                risk_end = risk_start + 150000
            sections["risk_factors"] = full_text[risk_start:risk_end].strip()

        # Cybersecurity
        cyber_match = re.search(r"Item\s*1C\.?\s*Cybersecurity", full_text, re.IGNORECASE)
        if cyber_match:
            cyber_start = cyber_match.start()
            cyber_end = full_text.find("Item 2", cyber_start + 100)
            if cyber_end > cyber_start:
                sections["cybersecurity"] = full_text[cyber_start:cyber_end].strip()

        # Competition subsection - try multiple patterns
        comp_patterns = [
            "Competition\nThe market for our products",
            "Competition\nThe market for",
            "Competition \nThe market",
        ]
        comp_start = -1
        for pattern in comp_patterns:
            comp_start = full_text.find(pattern)
            if comp_start > 0:
                break

        # Also try regex for more flexibility
        if comp_start == -1:
            comp_match = re.search(r"Competition\s+The market for", full_text, re.IGNORECASE)
            if comp_match:
                comp_start = comp_match.start()

        if comp_start > 0:
            comp_end = full_text.find("Patents and Proprietary", comp_start)
            if comp_end == -1:
                comp_end = full_text.find("Patents and Proprietary Rights", comp_start)
            if comp_end == -1:
                comp_end = comp_start + 5000  # Fallback: take 5K chars
            if comp_end > comp_start:
                sections["competition"] = full_text[comp_start:comp_end].strip()

        return sections


sec_client = SECClient()
