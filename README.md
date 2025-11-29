# SEC Tracker

API for extracting structured insights from SEC 10-K filings using LLMs.

## Features

- **AI Trend Analysis**: Track how companies discuss AI across multiple years of filings
- **Competitive Intelligence**: Extract named competitors and competitive factors
- **Risk Assessment**: Categorize disclosed risk factors
- **Cybersecurity Governance**: Analyze security frameworks and board oversight
- **Smart Ticker Lookup**: Resolve brands and subsidiaries to SEC tickers (e.g., "YouTube" → GOOGL)

## Quick Start

```bash
# Clone and install
git clone https://github.com/sidscorp/sec-tracker.git
cd sec-tracker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export OPENROUTER_API_KEY=your_key_here
export OPENROUTER_MODEL=google/gemini-2.0-flash-001
export SEC_USER_AGENT="YourApp contact@example.com"

# Run
uvicorn app.main:app --reload --port 8001
```

## API Examples

### AI Deep Dive
```bash
curl "http://localhost:8001/api/extract/NVDA/ai"
```

Returns AI products, risks, investments, competitive positioning, and key strategic quotes from the latest 10-K.

### Historical AI Trends
```bash
curl "http://localhost:8001/api/extract/NVDA/ai/history?years=5"
```

Analyzes 5 years of filings in parallel (~12s). Returns year-over-year AI mention counts and narrative stance evolution.

### Company Lookup
```bash
curl "http://localhost:8001/api/lookup?q=instagram"
# Returns: META
```

### Other Extractions
```bash
curl "http://localhost:8001/api/extract/AAPL/competitors"
curl "http://localhost:8001/api/extract/AAPL/cybersecurity"
curl "http://localhost:8001/api/extract/AAPL/risks"
curl "http://localhost:8001/api/extract/AAPL/business"
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | API key from [OpenRouter](https://openrouter.ai/keys) | required |
| `OPENROUTER_MODEL` | LLM model ID | `anthropic/claude-3.5-sonnet` |
| `SEC_USER_AGENT` | Required by SEC API | `sec-tracker contact@example.com` |

### Recommended Models

| Model | Cost (input/output per 1M) | Notes |
|-------|---------------------------|-------|
| `google/gemini-2.0-flash-001` | $0.10 / $0.40 | Fast, 1M context, good value |
| `anthropic/claude-3.5-sonnet` | $3.00 / $15.00 | Highest quality |
| `anthropic/claude-3-haiku` | $0.25 / $1.25 | Budget option |

## Documentation

- [Design Document](docs/design.md) - Architecture and implementation details
- [SEC EDGAR API Reference](docs/sec-edgar-api.md) - Upstream API documentation

## License

MIT
