# SEC Tracker - Design Document

## 1. Introduction

The proliferation of artificial intelligence across industries has created a pressing need for systematic analysis of how public companies communicate their AI strategies to investors. SEC 10-K filings represent a rich, standardized corpus of corporate disclosures, yet extracting structured insights from these documents has traditionally required substantial manual effort.

SEC Tracker addresses this challenge by combining the SEC's public EDGAR API with large language models to automate the extraction of strategic intelligence from annual reports. The system provides a REST API that enables programmatic access to competitive analysis, risk assessment, and trend identification across any publicly traded company.

## 2. System Architecture

The application follows a layered architecture pattern, separating concerns across distinct service boundaries. At its foundation, the SEC client module manages all interactions with the EDGAR API, handling rate limiting, document retrieval, and section parsing. Above this, the extraction service orchestrates LLM-based analysis, transforming unstructured filing text into structured JSON responses. The API layer exposes these capabilities through a RESTful interface built on FastAPI.

```
sec-tracker/
├── app/
│   ├── api/routes.py           # HTTP endpoint definitions
│   ├── core/
│   │   ├── config.py           # Environment-based configuration
│   │   └── llm.py              # LLM client with observability
│   ├── services/
│   │   ├── sec_client.py       # EDGAR API integration
│   │   ├── extraction.py       # Document analysis pipelines
│   │   ├── ticker_lookup.py    # Entity resolution service
│   │   └── wikidata.py         # Knowledge graph integration
│   └── models/schemas.py       # Response type definitions
└── docs/
    ├── design.md               # This document
    └── sec-edgar-api.md        # EDGAR API reference
```

## 3. SEC EDGAR Integration

The SEC client module provides a comprehensive interface to the EDGAR system. Company metadata retrieval leverages the submissions API, which returns filing histories spanning decades for established corporations. Document retrieval follows a two-stage process: first identifying the appropriate filing through the submissions index, then fetching the primary document from the SEC archives.

Section extraction presents particular challenges given the lack of standardization in 10-K formatting. The implementation employs a series of regular expression patterns targeting Item headers as defined by SEC regulations. The system extracts five primary sections of interest: the business description (Item 1), risk factors (Item 1A), cybersecurity disclosures (Item 1C, a recent regulatory addition), management discussion and analysis (Item 7), and competitive positioning (typically a subsection within Item 1).

Historical analysis is supported through fiscal year-specific retrieval. The client maintains an index of available filings per company, enabling longitudinal studies of corporate disclosure evolution.

## 4. LLM Integration and Cost Management

The system interfaces with language models through OpenRouter, a unified gateway supporting multiple providers including Anthropic, Google, and OpenAI. This abstraction enables model selection based on cost-performance tradeoffs without code modifications.

A central design consideration was observability of LLM usage. Each request is logged with a unique identifier, enabling correlation between API calls and their corresponding model invocations. The client tracks token consumption and computes costs based on published model pricing, aggregating these metrics into session-level statistics. This instrumentation proves essential for capacity planning and cost optimization in production deployments.

The extraction interface provides both synchronous and asynchronous methods. Async support enables parallel processing of multiple documents, a critical capability for historical trend analysis where sequential processing would introduce unacceptable latency.

## 5. Extraction Methodology

Document analysis proceeds through structured prompting with JSON schema constraints. Each extraction type defines an explicit output schema, guiding the model toward consistent, machine-parseable responses. The system handles common LLM output variations including markdown code blocks and extraneous formatting.

The AI-focused extraction represents the most comprehensive analysis pipeline. It evaluates corporate AI positioning across seven dimensions: narrative stance (whether the company frames AI as opportunity, risk, or both), product and service offerings, disclosed risks categorized by type, investment signals including infrastructure and partnerships, competitive positioning claims, quantitative metrics, and notable strategic statements. Additionally, a regex-based counter tallies AI-related terminology to provide a simple frequency metric independent of LLM interpretation.

Context window management leverages modern large-context models. The system transmits up to 195,000 characters of filing text per extraction, comprising 80,000 from the business section, 60,000 from risk factors, 40,000 from MD&A, and 15,000 from competition discussions. This generous context allocation ensures the model has access to comprehensive source material while remaining within token limits of 1M-token models.

## 6. Entity Resolution

Company identification presents a non-trivial challenge given the diversity of corporate naming conventions. A user searching for "YouTube" expects resolution to Alphabet Inc., while "Instagram" should map to Meta Platforms.

The ticker lookup service implements a cascading resolution strategy. Direct matching attempts fuzzy string comparison against the SEC's canonical company name registry. When this fails, the system queries Wikidata's knowledge graph, which maintains subsidiary and parent company relationships. This enables resolution of well-known brands to their SEC-reporting parent entities. A final LLM-based fallback handles edge cases including misspellings and informal brand references.

## 7. Parallel Processing Architecture

Historical trend analysis requires extracting data from multiple annual filings, each involving substantial document retrieval and LLM processing. Sequential execution of five-year analyses proved prohibitively slow during initial testing, with total latencies exceeding 45 seconds.

The implemented solution employs Python's asyncio for concurrent execution. Document preparation (SEC API calls and section extraction) runs in a thread pool executor to avoid blocking the event loop. LLM calls proceed through the async client interface. Using asyncio.gather(), all year-specific extractions execute in parallel, reducing wall-clock time to approximately that of a single extraction regardless of the number of years analyzed.

Empirical testing demonstrates consistent performance: a five-year analysis completes in approximately 12 seconds, achieving a 4x speedup over sequential processing.

## 8. API Design

The REST API follows resource-oriented conventions. Company lookup endpoints support both search (returning ranked results) and resolution (returning a single best match). Extraction endpoints are organized under a common prefix with the ticker symbol as a path parameter.

All extraction responses include the extracted data alongside LLM metrics (model used, token counts, cost, latency). This transparency enables clients to monitor usage and make informed decisions about extraction frequency and caching strategies.

A dedicated monitoring endpoint exposes aggregated session statistics, facilitating integration with external observability platforms.

## 9. Configuration and Deployment

The application follows twelve-factor principles, deriving all configuration from environment variables. Required settings include the OpenRouter API key; optional settings control model selection, logging verbosity, and SEC API identification.

The SEC requires all API consumers to identify themselves via the User-Agent header. Failure to provide meaningful contact information may result in rate limiting or blocking. The system includes a configurable user agent that should be updated with appropriate contact details for production deployments.

## 10. Future Directions

Several extensions merit consideration for future development. Database integration would enable caching of extracted data, reducing both latency and API costs for repeated queries. Batch processing capabilities would support portfolio-wide analysis across multiple tickers. Additional extraction schemas could address ESG disclosures, executive compensation structures, and segment-level financial breakdowns. Webhook integration would enable event-driven architectures triggered by new filing publications.

The modular architecture facilitates these extensions without fundamental restructuring, as each represents a natural evolution of existing service boundaries.
