-- PostgreSQL initial schema for Thesis Defense Agent.
-- This migration is intentionally idempotent so it can be used for local
-- integration testing before a full migration runner is introduced.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS defense_tasks (
    task_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    status TEXT NOT NULL,
    current_step_id TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_defense_tasks_status
    ON defense_tasks (status);

CREATE INDEX IF NOT EXISTS idx_defense_tasks_updated_at
    ON defense_tasks (updated_at);

CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated_at
    ON agent_sessions (updated_at);

CREATE TABLE IF NOT EXISTS trace_records (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT,
    event_type TEXT,
    success BOOLEAN,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trace_records_source
    ON trace_records (source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_trace_records_created_at
    ON trace_records (created_at);

CREATE TABLE IF NOT EXISTS feedback_records (
    feedback_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_records_source
    ON feedback_records (source_type, source_id);

CREATE TABLE IF NOT EXISTS benchmark_candidates (
    candidate_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_benchmark_candidates_status
    ON benchmark_candidates (status);
