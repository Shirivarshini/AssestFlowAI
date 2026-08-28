-- Additive PostgreSQL migration for existing AssetFlow databases.
-- New installations receive these columns through SQLAlchemy create_all.
ALTER TABLE financing_transactions ADD COLUMN IF NOT EXISTS collateral_reference VARCHAR;
ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS trigger VARCHAR;
ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS lifecycle_stage VARCHAR;
ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS asset_value DOUBLE PRECISION;
ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS risk_score DOUBLE PRECISION;
ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS existing_exposure DOUBLE PRECISION;
ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS maximum_safe_exposure DOUBLE PRECISION;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS related_event_id VARCHAR;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS related_decision_id VARCHAR;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS actor_type VARCHAR NOT NULL DEFAULT 'SYSTEM';
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS actor_id VARCHAR;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS before_state JSON;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS after_state JSON;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS source_refs JSON;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS related_event_id VARCHAR;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS related_decision_id VARCHAR;
