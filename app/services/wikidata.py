"""Wikidata client for company ownership/subsidiary lookups."""
import httpx

USER_AGENT = "sec-tracker research@example.com"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData"

# Wikidata property IDs
P_OWNED_BY = "P127"
P_PARENT_ORG = "P749"
P_STOCK_EXCHANGE = "P414"
P_TICKER = "P249"
P_ISIN = "P946"


class WikidataClient:
    """Client for querying Wikidata company/ownership data."""

    def __init__(self):
        self._http = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """
        Search Wikidata for entities matching query.

        Returns list of dicts with: id, label, description
        """
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json",
            "limit": limit,
        }
        response = self._http.get(WIKIDATA_API, params=params)
        response.raise_for_status()

        results = []
        for item in response.json().get("search", []):
            results.append({
                "qid": item["id"],
                "label": item.get("label", ""),
                "description": item.get("description", ""),
            })
        return results

    def get_entity(self, qid: str) -> dict | None:
        """
        Get full entity data for a Wikidata QID.

        Returns dict with: qid, label, claims (parsed)
        """
        url = f"{WIKIDATA_ENTITY}/{qid}.json"
        response = self._http.get(url)
        if response.status_code != 200:
            return None

        data = response.json()
        entity = data.get("entities", {}).get(qid)
        if not entity:
            return None

        return {
            "qid": qid,
            "label": self._get_label(entity),
            "owners": self._get_claim_qids(entity, P_OWNED_BY),
            "parents": self._get_claim_qids(entity, P_PARENT_ORG),
            "exchanges": self._get_claim_qids(entity, P_STOCK_EXCHANGE),
            "ticker": self._get_claim_value(entity, P_TICKER),
            "isin": self._get_claim_value(entity, P_ISIN),
        }

    def find_public_parent(self, qid: str, max_depth: int = 5) -> dict | None:
        """
        Traverse ownership chain to find the publicly traded parent company.

        Args:
            qid: Starting Wikidata entity ID (e.g., "Q1049511" for WhatsApp)
            max_depth: Maximum levels to traverse

        Returns dict with:
            - qid: Wikidata ID of public parent
            - label: Company name
            - ticker: Stock ticker (if available in Wikidata)
            - isin: ISIN code (if available)
            - chain: List of company names in ownership chain
        """
        visited = set()
        current_qid = qid
        chain = []

        for _ in range(max_depth):
            if current_qid in visited:
                break
            visited.add(current_qid)

            entity = self.get_entity(current_qid)
            if not entity:
                break

            chain.append(entity["label"])

            # Check if publicly traded (has stock exchange)
            if entity["exchanges"]:
                return {
                    "qid": current_qid,
                    "label": entity["label"],
                    "ticker": entity["ticker"],
                    "isin": entity["isin"],
                    "chain": chain,
                }

            # Follow ownership chain: prefer "owned by" over "parent org"
            next_qid = None
            if entity["owners"]:
                next_qid = entity["owners"][0]
            elif entity["parents"]:
                next_qid = entity["parents"][0]

            if not next_qid:
                break
            current_qid = next_qid

        return None

    def lookup_subsidiary(self, query: str) -> dict | None:
        """
        Full lookup: search query → find entity → traverse to public parent.

        Args:
            query: Company/product name (e.g., "WhatsApp", "Instagram")

        Returns dict with:
            - query: Original search query
            - wikidata_match: Initial Wikidata match info
            - public_parent: Name of publicly traded parent
            - ticker: Ticker if available in Wikidata
            - chain: Ownership chain
        """
        # Search for entity
        results = self.search(query, limit=3)
        if not results:
            return None

        # Try each result until we find one with a public parent
        for match in results:
            parent_info = self.find_public_parent(match["qid"])
            if parent_info:
                return {
                    "query": query,
                    "wikidata_match": match,
                    "public_parent": parent_info["label"],
                    "ticker": parent_info["ticker"],
                    "isin": parent_info["isin"],
                    "chain": parent_info["chain"],
                }

        return None

    def _get_label(self, entity: dict) -> str:
        """Extract English label from entity."""
        return entity.get("labels", {}).get("en", {}).get("value", "Unknown")

    def _get_claim_qids(self, entity: dict, prop: str) -> list[str]:
        """Extract QID values from a claim property."""
        claims = entity.get("claims", {})
        if prop not in claims:
            return []

        qids = []
        for claim in claims[prop]:
            mainsnak = claim.get("mainsnak", {})
            if "datavalue" in mainsnak:
                value = mainsnak["datavalue"].get("value", {})
                if isinstance(value, dict) and "id" in value:
                    qids.append(value["id"])
        return qids

    def _get_claim_value(self, entity: dict, prop: str) -> str | None:
        """Extract first string value from a claim property."""
        claims = entity.get("claims", {})
        if prop not in claims:
            return None

        for claim in claims[prop]:
            mainsnak = claim.get("mainsnak", {})
            if "datavalue" in mainsnak:
                value = mainsnak["datavalue"].get("value")
                if isinstance(value, str):
                    return value
        return None


# Singleton instance
wikidata_client = WikidataClient()
