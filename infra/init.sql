-- Varuna — Day 0 initial schema
-- Covers: Identity & Conversation + Agent Execution Trace panels
-- (the two panels needed before any agent can actually run and log something)
-- Spatial/Environmental/Vessels/RAG tables get added as those agents come online —
-- don't build all 20 tables from the full schema poster on Day 0, only what's needed
-- to get the Planner + one agent running end-to-end.

CREATE EXTENSION IF NOT EXISTS postgis;
-- pgvector needs a different setup than the plain postgis image —
-- TODO (Prapti, when RAG Agent data layer starts): either switch to
-- `pgvector/pgvector:pg16` combined with postgis, or install the extension
-- manually. Not needed for Day 0.

-- ── Identity & Conversation ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT,
    preferred_lang TEXT DEFAULT 'en',
    home_port_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    started_at TIMESTAMPTZ DEFAULT now(),
    last_message_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role TEXT NOT NULL,          -- 'user' | 'assistant'
    content TEXT NOT NULL,
    detected_lang TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── Agent Execution Trace ──────────────────────────────────────────────
-- This is what backend/schemas/envelope.py::AgentEnvelope persists to.
-- Every agent call MUST write a row here — this is the explainability
-- trail and the debugging trail in one.

CREATE TABLE IF NOT EXISTS query_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id),
    intent TEXT,                 -- 'safety_check' | 'find_fishing_zone' | 'route_request' | 'regulation_question'
    status TEXT DEFAULT 'running',
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_run_id UUID REFERENCES query_runs(id),
    agent_name TEXT NOT NULL,    -- matches AgentEnvelope.agent
    input_params JSONB,
    output_data JSONB,           -- matches AgentEnvelope.data
    confidence NUMERIC,
    source TEXT,                 -- matches AgentEnvelope.source
    status TEXT,                 -- 'success' | 'error' | 'degraded'
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS risk_verdicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_run_id UUID REFERENCES query_runs(id),
    verdict TEXT NOT NULL,       -- 'SAFE' | 'CAUTION' | 'UNSAFE'
    rule_trace JSONB NOT NULL,   -- full threshold-by-threshold breakdown — NEVER LLM-generated
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes worth having from day 1
CREATE INDEX IF NOT EXISTS idx_agent_runs_query_run_id ON agent_runs(query_run_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
