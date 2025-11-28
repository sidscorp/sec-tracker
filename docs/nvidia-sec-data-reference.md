# SEC EDGAR Data Available for NVIDIA (NVDA)

## Company Overview

| Field | Value |
|-------|-------|
| CIK | 0001045810 |
| Ticker | NVDA |
| Exchange | Nasdaq |
| SIC Code | 3674 - Semiconductors & Related Devices |
| State of Incorporation | Delaware |
| Fiscal Year End | January 25 |
| Category | Large accelerated filer |
| Address | 2788 San Tomas Expressway, Santa Clara, CA 95051 |
| Phone | 408-486-2000 |

---

## 1. Filing Types Available

### Primary Financial Filings

| Form | Description | Frequency | Data Available |
|------|-------------|-----------|----------------|
| **10-K** | Annual Report | Yearly | Complete financials, business description, risk factors, MD&A, auditor report |
| **10-Q** | Quarterly Report | 3x/year | Quarterly financials, MD&A updates, legal proceedings |
| **8-K** | Current Report | As needed | Material events (earnings, acquisitions, leadership, contracts) |

### Ownership & Governance

| Form | Description | Data Available |
|------|-------------|----------------|
| **4** | Insider Transactions | Stock buys/sells by officers, directors, 10%+ owners |
| **144** | Restricted Stock Sale | Notice of proposed restricted stock sales |
| **DEF 14A** | Proxy Statement | Executive compensation, board composition, shareholder proposals |
| **13F-HR** | Institutional Holdings | NVIDIA's own institutional holdings (as filer) |
| **SC 13G** | Beneficial Ownership | Filed BY institutions owning 5%+ of NVIDIA |

### Other Filings

| Form | Description |
|------|-------------|
| **S-8** | Securities Registration (stock comp plans) |
| **SD** | Conflict Minerals Disclosure |
| **ARS** | Annual Report to Shareholders |
| **CORRESP** | SEC correspondence |

---

## 2. XBRL Financial Data (619 Concepts Available)

### Taxonomies

- **us-gaap**: 615 financial concepts (US GAAP accounting standards)
- **dei**: 2 concepts (Document & Entity Information)
- **srt**: 1 concept (SEC Reporting Taxonomy)
- **invest**: 1 concept (Investment data)

### Financial Data Categories

| Category | Concepts | Examples |
|----------|----------|----------|
| Income/Earnings | 90 | NetIncomeLoss, GrossProfit, OperatingIncomeLoss |
| Equity/Stock | 76 | StockholdersEquity, CommonStock, TreasuryStock |
| Assets | 67 | TotalAssets, CurrentAssets, PropertyPlantEquipment |
| Shares | 53 | SharesOutstanding, WeightedAverageShares |
| Expenses/Costs | 50 | R&D Expense, SG&A, CostOfRevenue |
| Debt | 43 | LongTermDebt, ShortTermDebt, DebtInstruments |
| Liabilities | 41 | TotalLiabilities, CurrentLiabilities |
| Cash | 17 | CashAndEquivalents, CashFromOperations |
| Revenue/Sales | 14 | Revenues, ProductRevenue, ServiceRevenue |
| Tax | 12 | IncomeTaxExpense, DeferredTaxAssets |

### Key Financial Metrics (with Historical Data)

#### Income Statement
| Metric | FY2025 | FY2024 | FY2023 |
|--------|--------|--------|--------|
| Revenue | $130.5B | $60.9B | $27.0B |
| Gross Profit | $97.9B | $44.3B | $15.4B |
| Operating Income | $81.5B | $33.0B | $4.2B |
| Net Income | $72.9B | $29.8B | $4.4B |
| R&D Expense | $12.9B | $8.7B | $7.3B |
| EPS (Diluted) | $2.94 | $1.19 | $0.17 |

#### Balance Sheet
| Metric | FY2025 | FY2024 | FY2023 |
|--------|--------|--------|--------|
| Total Assets | $111.6B | $65.7B | $41.2B |
| Total Liabilities | $32.3B | $22.8B | $19.1B |
| Stockholders' Equity | $79.3B | $43.0B | $22.1B |
| Cash & Equivalents | $8.6B | $7.3B | $3.4B |
| Long-term Debt | $8.5B | $9.7B | $11.0B |

#### Per-Share Data
| Metric | Latest |
|--------|--------|
| Shares Outstanding | 24.5B |
| EPS Basic | $2.97 |
| EPS Diluted | $2.94 |

---

## 3. Filing Documents Structure

Each filing contains multiple documents:

### 10-K Annual Report Documents
```
nvda-20250126.htm          - Main filing (HTML, ~2MB)
Financial_Report.xlsx      - Excel version of financials
nvda-20250126_htm.xml      - XBRL instance document
nvda-20250126_cal.xml      - XBRL calculation linkbase
nvda-20250126_def.xml      - XBRL definition linkbase
nvda-20250126_lab.xml      - XBRL label linkbase
nvda-20250126_pre.xml      - XBRL presentation linkbase
nvda-20250126.xsd          - XBRL schema
MetaLinks.json             - XBRL metadata
FilingSummary.xml          - Filing structure
*.jpg                      - Charts and images
ex*.htm                    - Exhibits (contracts, certifications)
```

### Document Access URLs
```
Base: https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/
Example: https://www.sec.gov/Archives/edgar/data/1045810/000104581025000023/nvda-20250126.htm
```

---

## 4. Available Data via API Endpoints

### Submissions API
```
URL: https://data.sec.gov/submissions/CIK0001045810.json
```
Returns:
- Company metadata (name, CIK, SIC, addresses)
- Ticker symbols and exchanges
- Filing history (1000+ recent filings)
- Accession numbers for document access

### Company Facts API
```
URL: https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json
```
Returns:
- All 619 XBRL financial concepts
- Historical values going back 10+ years
- Values from 10-K, 10-Q, and other filings
- Multiple units (USD, shares, pure ratios)

### Company Concept API
```
URL: https://data.sec.gov/api/xbrl/companyconcept/CIK0001045810/us-gaap/{concept}.json
Example: .../us-gaap/Revenues.json
```
Returns:
- Single concept with full history
- All reported values across filings
- Filing metadata (form type, date, accession)

---

## 5. Top 50 Financial Concepts by Data Availability

| Concept | Data Points | Unit |
|---------|-------------|------|
| EarningsPerShareBasic | 300 | USD/share |
| EarningsPerShareDiluted | 300 | USD/share |
| NetIncomeLoss | 300 | USD |
| GrossProfit | 296 | USD |
| CostOfRevenue | 271 | USD |
| Revenues | 271 | USD |
| StockholdersEquity | 234 | USD |
| ProductWarrantyAccrual | 225 | USD |
| IncomeTaxExpenseBenefit | 222 | USD |
| WeightedAverageNumberOfDilutedSharesOutstanding | 222 | shares |
| InvestmentIncomeInterest | 216 | USD |
| OperatingExpenses | 216 | USD |
| OperatingIncomeLoss | 216 | USD |
| ResearchAndDevelopmentExpense | 216 | USD |
| SellingGeneralAndAdministrativeExpense | 216 | USD |
| CashAndCashEquivalentsAtCarryingValue | 213 | USD |
| EffectiveIncomeTaxRateContinuingOperations | 201 | pure |
| ComprehensiveIncomeNetOfTax | 197 | USD |
| ShareBasedCompensation | 186 | USD |
| AmortizationOfIntangibleAssets | 166 | USD |
| DepreciationAndAmortization | 150 | USD |
| CommonStockDividendsPerShareDeclared | 148 | USD/share |
| DeferredIncomeTaxExpenseBenefit | 148 | USD |
| IncreaseDecreaseInAccountsPayable | 148 | USD |
| IncreaseDecreaseInAccountsReceivable | 148 | USD |
| IncreaseDecreaseInInventories | 148 | USD |
| NetCashProvidedByUsedInOperatingActivities | 154 | USD |
| NetCashProvidedByUsedInInvestingActivities | 148 | USD |
| NetCashProvidedByUsedInFinancingActivities | 154 | USD |
| PaymentsOfDividends | 148 | USD |
| InterestExpense | 147 | USD |
| AccountsPayableCurrent | 132 | USD |
| AccountsReceivableNetCurrent | 132 | USD |
| Assets | 132 | USD |
| Goodwill | 132 | USD |
| InventoryNet | 132 | USD |
| Liabilities | 132 | USD |
| LongTermDebt | 132 | USD |
| PropertyPlantAndEquipmentNet | 132 | USD |
| RetainedEarningsAccumulatedDeficit | 132 | USD |

---

## 6. 8-K Material Event Categories

Recent 8-K filings and their item codes:

| Item Code | Description | Recent Example |
|-----------|-------------|----------------|
| 2.02 | Results of Operations | Earnings announcements |
| 5.02 | Departure/Election of Officers | Leadership changes |
| 5.07 | Shareholder Vote Results | Annual meeting results |
| 9.01 | Financial Statements and Exhibits | Supporting documents |

---

## 7. Insider Trading Data (Form 4)

Available for each transaction:
- Reporting person (name, relationship)
- Transaction date
- Securities type (common stock, options, RSUs)
- Transaction type (purchase, sale, grant, exercise)
- Shares transacted
- Price per share
- Shares owned after transaction

---

## 8. Rate Limits & Best Practices

- **Rate Limit**: 10 requests/second
- **Required Header**: `User-Agent: AppName contact@email.com`
- **Data Freshness**: Real-time (submissions updated within seconds of filing)
- **Bulk Downloads**: Available at `https://www.sec.gov/Archives/edgar/full-index/`

---

## 9. Data Not Available via SEC API

- Real-time stock prices (use market data providers)
- Analyst estimates/ratings
- Non-GAAP metrics (though some appear in filings)
- Segment revenue by product line (limited, varies by company)
- Customer concentration details (often redacted)
- Forward guidance (in 8-K text, not structured data)
