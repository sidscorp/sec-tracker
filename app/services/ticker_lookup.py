"""
Smart ticker lookup service.

Combines multiple strategies to resolve company names/queries to SEC tickers:
1. Direct SEC match (rapidfuzz) - fast, for obvious matches
2. Wikidata subsidiary lookup - for subsidiaries/brands → parent company
3. LLM fallback - for typos, brand aliases not in Wikidata
"""
from dataclasses import dataclass
from enum import Enum

from rapidfuzz import fuzz, process

from app.core.llm import llm_client
from app.services.sec_client import sec_client
from app.services.wikidata import wikidata_client


class LookupMethod(str, Enum):
    """How the ticker was resolved."""
    DIRECT = "direct"           # Direct SEC name match (rapidfuzz)
    WIKIDATA = "wikidata"       # Via Wikidata subsidiary → parent lookup
    LLM = "llm"                 # LLM identified the company
    FALLBACK = "fallback"       # Best guess from rapidfuzz (low confidence)


@dataclass
class LookupResult:
    """Result of a ticker lookup."""
    query: str
    ticker: str | None
    company_name: str | None
    method: LookupMethod
    confidence: float
    chain: list[str] | None = None  # Ownership chain for subsidiary lookups


# Confidence thresholds
DIRECT_MATCH_THRESHOLD = 0.85   # rapidfuzz score to accept without LLM
SEC_MATCH_THRESHOLD = 0.70      # Minimum score to match Wikidata result to SEC


class TickerLookupService:
    """
    Service for resolving company names to SEC tickers.

    Uses a multi-stage approach:
    1. Try direct rapidfuzz match against SEC company names
    2. If low confidence, try Wikidata for subsidiary → parent lookup
    3. If still unresolved, ask LLM to identify the company
    """

    def __init__(self):
        self._sec_names: list[str] | None = None
        self._sec_name_to_tickers: dict[str, list[dict]] | None = None

    def _ensure_sec_data(self):
        """Load and cache SEC company data for fuzzy matching."""
        if self._sec_names is not None:
            return

        ticker_map = sec_client._get_ticker_map()
        self._sec_name_to_tickers = {}
        for info in ticker_map.values():
            name_upper = info["title"].upper()
            ticker_info = {
                "ticker": info["ticker"],
                "name": info["title"],
                "cik": str(info["cik_str"]).zfill(10),
            }
            if name_upper not in self._sec_name_to_tickers:
                self._sec_name_to_tickers[name_upper] = []
            self._sec_name_to_tickers[name_upper].append(ticker_info)
        self._sec_names = list(self._sec_name_to_tickers.keys())

    def _fuzzy_match_sec(
        self, query: str, limit: int = 5
    ) -> list[tuple[str, str, str, float]]:
        """
        Fuzzy match query against SEC company names.

        Returns list of (ticker, name, cik, score) tuples.
        Includes all tickers for companies with multiple share classes (e.g., GOOG/GOOGL).
        """
        self._ensure_sec_data()

        results = process.extract(
            query.upper(),
            self._sec_names,
            scorer=fuzz.token_set_ratio,
            limit=limit,
        )

        matches = []
        for name, score, _ in results:
            for info in self._sec_name_to_tickers[name]:
                matches.append((
                    info["ticker"],
                    info["name"],
                    info["cik"],
                    score / 100,
                ))
        return matches

    def _llm_identify_company(self, query: str) -> str | None:
        """
        Ask LLM to identify the official SEC company name.

        Returns the company name as it appears in SEC filings, or None.
        """
        prompt = f'''The user is searching for a publicly traded US company: "{query}"

What is the official legal name of the company they're looking for, as it would appear in SEC filings?

Consider:
- Brand names vs parent companies (Google → Alphabet Inc., Facebook/Instagram → Meta Platforms, Inc.)
- Common abbreviations (AWS → Amazon.com, Inc.)
- Typos and misspellings
- The company must be publicly traded on a US exchange

Respond with ONLY the company's official SEC filing name, nothing else.
If you cannot determine the company, respond with "UNKNOWN".'''

        response = llm_client.complete(
            prompt=prompt,
            model="anthropic/claude-3-haiku",
            max_tokens=50,
            metadata={"task": "ticker_lookup"},
        )

        if response.error:
            return None

        name = response.content.strip()
        if name.upper() == "UNKNOWN":
            return None
        return name

    def lookup(self, query: str) -> LookupResult:
        """
        Resolve a company name/query to an SEC ticker.

        Args:
            query: Company name, brand name, subsidiary, or ticker

        Returns:
            LookupResult with ticker, company name, method used, and confidence
        """
        query = query.strip()
        if not query:
            return LookupResult(
                query=query,
                ticker=None,
                company_name=None,
                method=LookupMethod.FALLBACK,
                confidence=0.0,
            )

        # Stage 1: Direct rapidfuzz match
        direct_matches = self._fuzzy_match_sec(query, limit=5)
        if direct_matches:
            top_ticker, top_name, _, top_score = direct_matches[0]

            if top_score >= DIRECT_MATCH_THRESHOLD:
                return LookupResult(
                    query=query,
                    ticker=top_ticker,
                    company_name=top_name,
                    method=LookupMethod.DIRECT,
                    confidence=top_score,
                )

        # Stage 2: Wikidata subsidiary lookup
        wikidata_result = wikidata_client.lookup_subsidiary(query)
        if wikidata_result:
            parent_name = wikidata_result["public_parent"]

            # Match parent name to SEC data
            sec_matches = self._fuzzy_match_sec(parent_name, limit=3)
            if sec_matches:
                best_ticker, best_name, _, best_score = sec_matches[0]

                # If Wikidata parent doesn't match SEC well, try going up the chain
                if best_score < SEC_MATCH_THRESHOLD and wikidata_result.get("chain"):
                    for chain_name in reversed(wikidata_result["chain"][:-1]):
                        alt_matches = self._fuzzy_match_sec(chain_name, limit=1)
                        if alt_matches and alt_matches[0][3] > best_score:
                            best_ticker, best_name, _, best_score = alt_matches[0]

                if best_score >= SEC_MATCH_THRESHOLD:
                    return LookupResult(
                        query=query,
                        ticker=best_ticker,
                        company_name=best_name,
                        method=LookupMethod.WIKIDATA,
                        confidence=0.9,
                        chain=wikidata_result.get("chain"),
                    )

        # Stage 3: LLM fallback
        llm_suggested_name = self._llm_identify_company(query)
        if llm_suggested_name:
            llm_matches = self._fuzzy_match_sec(llm_suggested_name, limit=3)
            if llm_matches and llm_matches[0][3] >= SEC_MATCH_THRESHOLD:
                ticker, name, _, _ = llm_matches[0]
                return LookupResult(
                    query=query,
                    ticker=ticker,
                    company_name=name,
                    method=LookupMethod.LLM,
                    confidence=0.85,
                )

        # Stage 4: Return best rapidfuzz match as fallback
        if direct_matches:
            top_ticker, top_name, _, top_score = direct_matches[0]
            return LookupResult(
                query=query,
                ticker=top_ticker,
                company_name=top_name,
                method=LookupMethod.FALLBACK,
                confidence=top_score,
            )

        return LookupResult(
            query=query,
            ticker=None,
            company_name=None,
            method=LookupMethod.FALLBACK,
            confidence=0.0,
        )

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for companies matching query.

        Returns list of matches with ticker, name, cik, match_type, score.
        For direct SEC matches, returns multiple results.
        For subsidiary/LLM lookups, returns single best match.
        """
        query = query.strip()
        if not query:
            return []

        # First, try smart lookup to handle subsidiaries/typos
        lookup_result = self.lookup(query)

        results = []

        # If smart lookup found something via Wikidata/LLM, include it first
        if lookup_result.ticker and lookup_result.method in (
            LookupMethod.WIKIDATA,
            LookupMethod.LLM,
        ):
            results.append({
                "ticker": lookup_result.ticker,
                "name": lookup_result.company_name,
                "cik": sec_client.ticker_to_cik(lookup_result.ticker),
                "match_type": lookup_result.method.value,
                "score": lookup_result.confidence,
                "chain": lookup_result.chain,
            })

        # Add direct fuzzy matches
        direct_matches = self._fuzzy_match_sec(query, limit=limit)
        seen_tickers = {r["ticker"] for r in results}

        for ticker, name, cik, score in direct_matches:
            if ticker not in seen_tickers:
                results.append({
                    "ticker": ticker,
                    "name": name,
                    "cik": cik,
                    "match_type": "direct",
                    "score": score,
                    "chain": None,
                })
                seen_tickers.add(ticker)

            if len(results) >= limit:
                break

        return results


# Singleton instance
ticker_lookup = TickerLookupService()
