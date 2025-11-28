# SEC EDGAR API Reference

## Overview

The SEC provides free, public API access to EDGAR filing data at `data.sec.gov`. No authentication required. Rate limit: 10 requests/second. Must include User-Agent header with contact info.

## Core APIs

### 1. Submissions API
**URL**: `https://data.sec.gov/submissions/CIK{cik}.json`

Returns company metadata and filing history.

**Response includes**:
- Company name, CIK, SIC code
- Tickers and exchanges
- Business/mailing addresses
- Filing history (up to 1000 recent filings)

**CIK Format**: 10 digits, zero-padded (e.g., `0000320193` for Apple)

### 2. Company Facts API
**URL**: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`

Returns all XBRL financial data for a company.

**Response includes**:
- All reported financial concepts (500+ for large companies)
- Historical values with filing dates
- Organized by taxonomy (us-gaap, dei, etc.)

### 3. Company Concept API
**URL**: `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json`

Returns historical values for a specific financial metric.

**Example**: `/CIK0000320193/us-gaap/Revenues.json`

**Common tags**:
- `Revenues`, `NetIncomeLoss`, `Assets`, `Liabilities`
- `StockholdersEquity`, `OperatingIncomeLoss`
- `CashAndCashEquivalentsAtCarryingValue`

### 4. Frames API
**URL**: `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`

Returns cross-company data for a specific metric and period.

**Period formats**:
- Annual: `CY2023`
- Quarterly: `CY2023Q1`
- Instantaneous: `CY2023Q1I`

## Lookup Endpoints

### Company Tickers
**URL**: `https://www.sec.gov/files/company_tickers.json`

Maps all public company tickers to CIK numbers.

### Exchange Tickers
**URL**: `https://www.sec.gov/files/company_tickers_exchange.json`

Tickers with exchange information (Nasdaq, NYSE, etc.)

## Filing Documents

**URL**: `https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}`

Access actual filing documents (10-K, 10-Q, 8-K, etc.)

**Accession format**: Remove dashes from accession number (e.g., `0000320193-24-000123` → `000032019324000123`)

## Common Filing Types

| Form | Description |
|------|-------------|
| 10-K | Annual report |
| 10-Q | Quarterly report |
| 8-K | Current report (material events) |
| 4 | Insider trading |
| 13F | Institutional holdings |
| DEF 14A | Proxy statement |
| S-1 | IPO registration |

## Rate Limits & Best Practices

1. Maximum 10 requests/second
2. Always include User-Agent header with company name and contact email
3. Cache ticker/CIK mappings locally
4. Use bulk downloads for large data needs:
   - `https://www.sec.gov/Archives/edgar/full-index/` (filing indices)
   - Submissions API returns paginated data via `filings.files` array

## Example Request Headers

```python
headers = {
    "User-Agent": "MyApp/1.0 (contact@example.com)"
}
```
