"""SEC EDGAR API client."""
import re
from functools import lru_cache

import httpx

from app.core.config import settings

HEADERS = {"User-Agent": settings.SEC_USER_AGENT}
BASE_URL = "https://data.sec.gov"
SEC_URL = "https://www.sec.gov"


def _normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    name = name.upper()
    name = re.sub(r"[.,']", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


class SECClient:
    def __init__(self):
        self._http = httpx.Client(headers=HEADERS, timeout=60)
        self._ticker_map: dict[str, dict] | None = None
        self._name_map: dict[str, list[dict]] | None = None

    def _get_ticker_map(self) -> dict[str, dict]:
        if self._ticker_map is None:
            url = f"{SEC_URL}/files/company_tickers.json"
            response = self._http.get(url)
            response.raise_for_status()
            data = response.json()
            self._ticker_map = {v["ticker"]: v for v in data.values()}
        return self._ticker_map

    def _get_name_map(self) -> dict[str, list[dict]]:
        """Build normalized name -> company info mapping."""
        if self._name_map is None:
            ticker_map = self._get_ticker_map()
            self._name_map = {}
            for info in ticker_map.values():
                normalized = _normalize_name(info["title"])
                if normalized not in self._name_map:
                    self._name_map[normalized] = []
                self._name_map[normalized].append(info)
        return self._name_map

    def ticker_to_cik(self, ticker: str) -> str | None:
        ticker_map = self._get_ticker_map()
        info = ticker_map.get(ticker.upper())
        if info:
            return str(info["cik_str"]).zfill(10)
        return None

    def search_by_name(self, query: str, limit: int = 10) -> list[dict]:
        """Search for companies by name. Returns list of matches."""
        name_map = self._get_name_map()
        query_normalized = _normalize_name(query)
        results = []

        # Exact match first
        if query_normalized in name_map:
            for info in name_map[query_normalized]:
                results.append({
                    "ticker": info["ticker"],
                    "name": info["title"],
                    "cik": str(info["cik_str"]).zfill(10),
                    "match_type": "exact",
                })

        # Prefix match
        for name, infos in name_map.items():
            if name.startswith(query_normalized) and name != query_normalized:
                for info in infos:
                    results.append({
                        "ticker": info["ticker"],
                        "name": info["title"],
                        "cik": str(info["cik_str"]).zfill(10),
                        "match_type": "prefix",
                    })

        # Contains match (if not enough results)
        if len(results) < limit:
            for name, infos in name_map.items():
                if query_normalized in name and not name.startswith(query_normalized):
                    for info in infos:
                        results.append({
                            "ticker": info["ticker"],
                            "name": info["title"],
                            "cik": str(info["cik_str"]).zfill(10),
                            "match_type": "contains",
                        })

        # Dedupe and limit
        seen = set()
        unique_results = []
        for r in results:
            if r["ticker"] not in seen:
                seen.add(r["ticker"])
                unique_results.append(r)
                if len(unique_results) >= limit:
                    break

        return unique_results

    def name_to_ticker(self, name: str) -> str | None:
        """Get best matching ticker for a company name."""
        results = self.search_by_name(name, limit=1)
        if results:
            return results[0]["ticker"]
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

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean text."""
        # Remove style and script tags
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Convert block elements to newlines
        text = re.sub(r"<(?:p|div|br|tr|h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&")
        text = re.sub(r"&#\d+;", " ", text)

        # Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _is_toc_content(self, content: str) -> bool:
        """
        Detect if content is Table of Contents rather than actual section content.

        TOC sections have many Item references with page numbers in a short span.
        """
        # Check first 2000 chars for TOC patterns
        sample = content[:2000]

        # Count Item references - TOC has many in quick succession
        item_refs = len(re.findall(r"Item\s*\d+[A-C]?\.?\s", sample, re.IGNORECASE))

        # TOC typically has 5+ Item references in the first 2000 chars
        if item_refs >= 5:
            return True

        # Also check for page number patterns (numbers on their own lines)
        page_nums = len(re.findall(r"\n\s*\d{1,3}\s*\n", sample))
        if page_nums >= 3 and item_refs >= 3:
            return True

        return False

    def _find_section(
        self,
        text: str,
        start_pattern: str,
        end_pattern: str,
        min_length: int = 1000,
    ) -> str | None:
        """
        Extract section between start and end patterns.

        Skips Table of Contents entries by:
        1. Requiring minimum content length
        2. Detecting TOC-like content (many Item references)
        """
        start_matches = list(re.finditer(start_pattern, text, re.IGNORECASE))
        if not start_matches:
            return None

        end_matches = list(re.finditer(end_pattern, text, re.IGNORECASE))

        # Try each start match to find one with substantial content
        for start_match in start_matches:
            start_pos = start_match.end()

            # Find the next end marker after this start
            end_pos = None
            for end_match in end_matches:
                if end_match.start() > start_pos + min_length:
                    end_pos = end_match.start()
                    break

            if end_pos is None:
                # No end marker found, take a reasonable chunk
                end_pos = min(start_pos + 150000, len(text))

            content = text[start_pos:end_pos].strip()

            # Skip if too short
            if len(content) < min_length:
                continue

            # Skip TOC-like content
            if self._is_toc_content(content):
                continue

            return content

        return None

    def extract_10k_sections(self, html: str) -> dict[str, str]:
        """
        Extract key sections from 10-K HTML.

        Uses standard Item markers to extract sections generically.
        Handles Table of Contents by requiring minimum content length.
        Handles formatting variations (e.g., "B USINESS" with spaces).
        """
        full_text = self._html_to_text(html)
        sections = {}

        # Patterns use \s* between letters to handle formatting like "B USINESS"
        # Item 1 - Business (ends at Item 1A)
        business = self._find_section(
            full_text,
            r"Item\s*1\.?\s*B\s*U\s*S\s*I\s*N\s*E\s*S\s*S",
            r"Item\s*1\s*A\.?\s*R\s*isk",
            min_length=2000,
        )
        if business:
            sections["business"] = business

        # Item 1A - Risk Factors (ends at Item 1B)
        risk_factors = self._find_section(
            full_text,
            r"Item\s*1\s*A\.?\s*R\s*I\s*S\s*K\s*F\s*A\s*C\s*T\s*O\s*R\s*S",
            r"Item\s*1\s*B\.?\s*U\s*nresolved",
            min_length=5000,
        )
        if risk_factors:
            sections["risk_factors"] = risk_factors

        # Item 1C - Cybersecurity (ends at Item 2)
        cybersecurity = self._find_section(
            full_text,
            r"Item\s*1\s*C\.?\s*C\s*Y\s*B\s*E\s*R\s*S\s*E\s*C\s*U\s*R\s*I\s*T\s*Y",
            r"Item\s*2\.?\s*P\s*roperties",
            min_length=500,
        )
        if cybersecurity:
            sections["cybersecurity"] = cybersecurity

        # Item 7 - MD&A (ends at Item 7A or Item 8)
        mdna = self._find_section(
            full_text,
            r"Item\s*7\.?\s*M\s*anagement.{0,50}D\s*iscussion",
            r"Item\s*(?:7\s*A|8)\.?",
            min_length=5000,
        )
        if mdna:
            sections["mdna"] = mdna

        # Competition subsection within Business section
        if business:
            comp_match = re.search(
                r"Competition\s*\n",
                business,
                re.IGNORECASE,
            )
            if comp_match:
                comp_start = comp_match.start()
                # Look for next section header or take ~5000 chars
                next_section = re.search(
                    r"\n(?:Seasonality|Government|Regulation|Employees|Human Capital|Intellectual Property|Patents)",
                    business[comp_start:],
                    re.IGNORECASE,
                )
                if next_section:
                    comp_end = comp_start + next_section.start()
                else:
                    comp_end = min(comp_start + 8000, len(business))
                sections["competition"] = business[comp_start:comp_end].strip()

        return sections


sec_client = SECClient()
