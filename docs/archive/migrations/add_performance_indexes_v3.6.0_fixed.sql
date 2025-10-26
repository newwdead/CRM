-- Performance Indexes Migration v3.6.0 (Fixed)
-- Phase 2.2: Database Optimization - Only missing indexes

-- ============================================
-- DUPLICATE_CONTACTS TABLE (fix column names)
-- ============================================
-- Already have: contact_id_1, contact_id_2
CREATE INDEX IF NOT EXISTS ix_duplicate_contacts_similarity ON duplicate_contacts (similarity_score DESC);
CREATE INDEX IF NOT EXISTS ix_duplicate_contacts_status_score ON duplicate_contacts (status, similarity_score DESC);

-- ============================================
-- AUDIT_LOGS TABLE (correct table name)
-- ============================================
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs (entity_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs (entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity ON audit_logs (entity_type, entity_id, timestamp DESC);

-- ============================================
-- OCR_CORRECTIONS TABLE
-- ============================================
CREATE INDEX IF NOT EXISTS ix_ocr_corrections_contact_id ON ocr_corrections (contact_id);
CREATE INDEX IF NOT EXISTS ix_ocr_corrections_created_at ON ocr_corrections (created_at DESC);

-- Note: two_factor_auth and two_factor_backup_codes already have all needed indexes

-- ============================================
-- VACUUM & ANALYZE (PostgreSQL optimization)
-- ============================================
VACUUM ANALYZE contacts;
VACUUM ANALYZE users;
VACUUM ANALYZE duplicate_contacts;
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE ocr_corrections;

