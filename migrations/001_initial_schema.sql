-- Initial schema for SEC AI Tracker
-- Run with: psql -d sec_tracker -f migrations/001_initial_schema.sql

-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    cik VARCHAR(10),
    name VARCHAR(255),
    sic VARCHAR(10),
    sic_description VARCHAR(255),
    fiscal_year_end VARCHAR(10),
    state_of_incorporation VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on ticker for fast lookups
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_companies_cik ON companies(cik);

-- Create AI extractions table
CREATE TABLE IF NOT EXISTS ai_extractions (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),

    -- Filing metadata
    filing_date DATE NOT NULL,
    fiscal_year VARCHAR(4) NOT NULL,

    -- Core AI analysis
    ai_narrative_stance VARCHAR(50) NOT NULL,  -- opportunity-focused, risk-focused, balanced, minimal
    ai_mention_count INTEGER DEFAULT 0,

    -- AI products and services (JSONB array)
    -- Each item: {name, description, monetization}
    ai_products_services JSONB DEFAULT '[]'::jsonb,

    -- AI risks disclosed (JSONB array)
    -- Each item: {risk, category}
    ai_risks_disclosed JSONB DEFAULT '[]'::jsonb,

    -- Investment signals
    infrastructure_mentions TEXT,
    partnerships TEXT[] DEFAULT '{}',
    acquisitions TEXT[] DEFAULT '{}',

    -- Competitive position
    claimed_advantages TEXT[] DEFAULT '{}',
    named_competitors TEXT[] DEFAULT '{}',
    market_position_claim TEXT,

    -- Metrics
    revenue_mentions TEXT,
    adoption_metrics TEXT,
    other_kpis TEXT[] DEFAULT '{}',

    -- Key quotes
    key_ai_quotes TEXT[] DEFAULT '{}',

    -- LLM metadata
    llm_model VARCHAR(100),
    llm_cost_usd REAL,
    llm_tokens INTEGER,

    -- Timestamps
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure one extraction per company per fiscal year
    CONSTRAINT uix_company_fiscal_year UNIQUE (company_id, fiscal_year)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ai_extractions_company_id ON ai_extractions(company_id);
CREATE INDEX IF NOT EXISTS idx_ai_extractions_fiscal_year ON ai_extractions(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_ai_extractions_stance ON ai_extractions(ai_narrative_stance);
CREATE INDEX IF NOT EXISTS idx_ai_extractions_mention_count ON ai_extractions(ai_mention_count);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for companies table
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
