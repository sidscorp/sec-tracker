# LLM Extraction Strategy for SEC 10-K Filings

## Executive Summary

After analyzing NVIDIA's 10-K filing, I've identified what structured information can be extracted from each unstructured section and the most efficient approach for LLM extraction.

**Key Insight**: Don't send entire sections to an LLM. Instead:
1. Pre-process sections to identify subsections
2. Use targeted extraction prompts per subsection type
3. Define strict output schemas to minimize token waste

---

## Section Analysis

### 1. Business Section (~40K chars, ~10K tokens)

**Content Structure**:
- Company overview paragraph
- Product/platform descriptions by segment
- Market descriptions (Data Center, Gaming, Professional Viz, Automotive)
- Business strategies (bulleted lists)
- Sales & marketing description
- Manufacturing & supply chain
- Competition section (with competitor lists)
- IP/Patents section
- Government regulations

**Extractable Structured Data**:

| Field | Type | Example |
|-------|------|---------|
| business_segments | list[str] | ["Compute & Networking", "Graphics"] |
| products | list[{name, category, description}] | [{name: "DGX Cloud", category: "Data Center", desc: "..."}] |
| markets | list[{name, description}] | [{name: "Data Center", desc: "..."}] |
| competitors | list[{name, category}] | [{name: "AMD", category: "GPU"}, {name: "Intel", category: "GPU"}] |
| key_customers | list[str] | ["CSPs", "enterprises", "startups"] |
| manufacturing_partners | list[{name, role}] | [{name: "TSMC", role: "foundry"}] |
| employee_count | int | 36000 |
| r&d_investment_total | float | 58.2B |

**Extraction Strategy**:
```
Split section into: Overview, Products, Markets, Competition, Manufacturing
For each subsection, use targeted prompt with schema
```

---

### 2. Risk Factors Section (~126K chars, ~31K tokens)

**Content Structure**:
- Risk summary (bulleted list of ~25 high-level risks)
- Detailed risk descriptions (each 200-500 words)
- Risks grouped by category:
  - Industry and Markets
  - Demand, Supply, Manufacturing
  - Global Operations
  - Regulatory, Legal, Stock

**Extractable Structured Data**:

| Field | Type | Example |
|-------|------|---------|
| risk_categories | list[str] | ["Industry", "Supply Chain", "Regulatory"] |
| risks | list[{title, category, severity, description_summary}] | [...] |
| key_dependencies | list[str] | ["TSMC", "Taiwan supply chain"] |
| regulatory_risks | list[{regulation, impact}] | [{reg: "US Export Controls", impact: "China revenue"}] |
| geographic_risks | list[str] | ["China", "Taiwan", "Asia-Pacific"] |

**Extraction Strategy**:
```
1. Extract risk summary section first (already bulleted, ~2K tokens)
2. For each risk in summary, extract: title, category, key entities mentioned
3. Skip detailed narrative unless specifically needed
```

**Token Efficiency**: Extract from the Risk Summary subsection (~3K tokens) instead of full section (31K tokens). Get 90% of value at 10% of cost.

---

### 3. Cybersecurity Section (~4K chars, ~1K tokens)

**Content Structure**:
- Risk management and strategy
- Governance structure
- Key personnel

**Extractable Structured Data**:

| Field | Type | Example |
|-------|------|---------|
| frameworks_used | list[str] | ["ISO 27001"] |
| has_cso | bool | true |
| cso_reports_to | str | "SVP of Software Engineering" |
| board_oversight | str | "Audit Committee" |
| vendor_assessment_process | bool | true |
| incident_response_team | bool | true |

**Extraction Strategy**:
```
Single prompt with full section - it's small enough
Define strict boolean/enum output schema
```

---

### 4. MD&A Section (~38K chars actual content, ~9.5K tokens)

**Content Structure**:
- Overview paragraph
- Recent developments and challenges
- Results of operations (by segment, by quarter)
- Financial condition discussion
- Liquidity and capital resources
- Critical accounting estimates

**Extractable Structured Data**:

| Field | Type | Example |
|-------|------|---------|
| key_drivers | list[str] | ["AI demand", "Data center growth", "Blackwell launch"] |
| challenges | list[str] | ["Export controls", "Supply constraints"] |
| segment_highlights | list[{segment, trend, driver}] | [...] |
| forward_guidance_signals | list[str] | ["Expect continued demand..."] |
| capital_allocation | {capex, dividends, buybacks} | {...} |
| liquidity_position | {cash, credit_facility} | {...} |

**Extraction Strategy**:
```
1. Extract Overview subsection for key themes (~2K tokens)
2. Extract Recent Developments for forward-looking signals (~2K tokens)
3. Skip detailed quarterly comparisons (use structured API data instead)
```

---

### 5. Legal Proceedings (if material)

**Extractable Data**:
- Active litigation cases
- Regulatory investigations
- Estimated liabilities

---

## Recommended Extraction Architecture

### Phase 1: Section Extraction (preprocessing)
```python
def extract_sections(html: str) -> dict[str, str]:
    """Extract major sections from 10-K HTML."""
    # Use regex patterns to find section boundaries
    # Return dict of section_name -> section_text
```

### Phase 2: Subsection Identification
```python
def identify_subsections(section: str, section_type: str) -> list[dict]:
    """Identify subsections within a major section."""
    # For Risk Factors: find "Risk Factors Summary" first
    # For Business: find segment headers
    # Return list of {name, start, end, text}
```

### Phase 3: Targeted Extraction
```python
EXTRACTION_SCHEMAS = {
    "business_overview": {
        "segments": "list[str]",
        "employee_count": "int",
        "headquarters": "str",
    },
    "competitors": {
        "competitors": "list[{name: str, category: str}]"
    },
    "risk_summary": {
        "risks": "list[{title: str, category: str}]"
    },
    # ...
}

def extract_with_llm(text: str, schema_name: str) -> dict:
    """Extract structured data using LLM with specific schema."""
    schema = EXTRACTION_SCHEMAS[schema_name]
    prompt = f"""Extract the following from this text.
    Output JSON matching this schema: {schema}

    Text:
    {text}
    """
    # Call LLM with structured output
```

---

## Token Cost Estimation

| Section | Full Tokens | Targeted Tokens | Savings |
|---------|-------------|-----------------|---------|
| Business | 10,000 | 3,000 | 70% |
| Risk Factors | 31,000 | 3,000 | 90% |
| Cybersecurity | 1,000 | 1,000 | 0% |
| MD&A | 9,500 | 4,000 | 58% |
| **Total** | **51,500** | **11,000** | **79%** |

---

## Output Schema Definitions

### CompanyOverview
```json
{
  "name": "string",
  "ticker": "string",
  "headquarters": "string",
  "employee_count": "integer",
  "fiscal_year_end": "string",
  "business_segments": ["string"],
  "key_products": [{"name": "string", "category": "string"}],
  "key_markets": ["string"]
}
```

### Competitors
```json
{
  "competitors": [
    {
      "name": "string",
      "category": "string (GPU|CPU|Cloud|Networking|Automotive)"
    }
  ]
}
```

### RiskSummary
```json
{
  "risk_categories": ["string"],
  "risks": [
    {
      "title": "string",
      "category": "string",
      "key_entities": ["string"],
      "geographic_exposure": ["string"]
    }
  ],
  "top_dependencies": ["string"]
}
```

### Cybersecurity
```json
{
  "frameworks": ["string"],
  "has_cso": "boolean",
  "cso_experience_years": "integer",
  "board_oversight": "string",
  "has_incident_response_team": "boolean",
  "has_vendor_risk_process": "boolean"
}
```

### ManagementOutlook
```json
{
  "key_drivers": ["string"],
  "challenges": ["string"],
  "forward_signals": ["string"],
  "recent_product_launches": ["string"]
}
```

---

## Implementation Recommendations

1. **Pre-split sections** before LLM calls to reduce context
2. **Use structured output** (JSON mode) to ensure parseable results
3. **Batch similar extractions** across multiple companies
4. **Cache extracted data** - 10-K content doesn't change after filing
5. **Validate outputs** against known facts from structured API
6. **Use smaller models** (e.g., GPT-4o-mini or Haiku) for simple extractions like Cybersecurity

### Cost-Benefit Priority

| Extraction | Value | Cost | Priority |
|------------|-------|------|----------|
| Competitors | High | Low | 1 |
| Risk Summary | High | Low | 2 |
| Cybersecurity | Medium | Very Low | 3 |
| Business Segments | Medium | Low | 4 |
| MD&A Outlook | High | Medium | 5 |
| Full Risk Details | Medium | High | 6 (skip) |
