-- Manual Migration: Add Two-Factor Authentication Tables
-- Version: v3.5.0
-- Date: 2025-10-24
-- Description: Add support for TOTP-based 2FA with backup codes

-- ============================================================================
-- Table: two_factor_auth
-- Purpose: Store TOTP secrets and 2FA configuration for users
-- ============================================================================

CREATE TABLE IF NOT EXISTS two_factor_auth (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- TOTP Configuration
    secret VARCHAR NOT NULL,  -- Base32 encoded TOTP secret
    is_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Backup codes (comma-separated, hashed)
    backup_codes TEXT,
    
    -- Metadata
    enabled_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_two_factor_auth_user_id ON two_factor_auth(user_id);
CREATE INDEX IF NOT EXISTS idx_two_factor_auth_is_enabled ON two_factor_auth(is_enabled);

-- Comments
COMMENT ON TABLE two_factor_auth IS 'Two-Factor Authentication configuration for users';
COMMENT ON COLUMN two_factor_auth.secret IS 'Base32 encoded TOTP secret for authenticator apps';
COMMENT ON COLUMN two_factor_auth.is_enabled IS 'Whether 2FA is currently active for this user';
COMMENT ON COLUMN two_factor_auth.backup_codes IS 'Deprecated: Use two_factor_backup_codes table instead';


-- ============================================================================
-- Table: two_factor_backup_codes
-- Purpose: Store individual backup recovery codes for 2FA
-- ============================================================================

CREATE TABLE IF NOT EXISTS two_factor_backup_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Backup code (hashed with SHA256)
    code_hash VARCHAR NOT NULL,
    
    -- Usage tracking
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_two_factor_backup_codes_user_id ON two_factor_backup_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_two_factor_backup_codes_is_used ON two_factor_backup_codes(is_used);
CREATE INDEX IF NOT EXISTS idx_two_factor_backup_codes_code_hash ON two_factor_backup_codes(code_hash);

-- Comments
COMMENT ON TABLE two_factor_backup_codes IS 'Individual backup codes for 2FA recovery';
COMMENT ON COLUMN two_factor_backup_codes.code_hash IS 'SHA256 hash of the backup code';
COMMENT ON COLUMN two_factor_backup_codes.is_used IS 'Whether this backup code has been used';


-- ============================================================================
-- Data Migration (if needed)
-- ============================================================================

-- No data migration needed for new tables


-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify tables exist
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('two_factor_auth', 'two_factor_backup_codes')
ORDER BY table_name;

-- Check indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('two_factor_auth', 'two_factor_backup_codes')
ORDER BY tablename, indexname;


-- ============================================================================
-- Rollback (if needed)
-- ============================================================================

-- DROP TABLE IF EXISTS two_factor_backup_codes CASCADE;
-- DROP TABLE IF EXISTS two_factor_auth CASCADE;


-- ============================================================================
-- Manual Application Instructions
-- ============================================================================

-- Option 1: Apply via psql
-- psql -U postgres -d bizcard_crm -f add_2fa_tables.sql

-- Option 2: Apply via Docker
-- docker exec -i bizcard-db psql -U postgres -d bizcard_crm < add_2fa_tables.sql

-- Option 3: Apply via pgAdmin
-- Copy and paste the CREATE TABLE statements into pgAdmin query tool

-- Option 4: Let SQLAlchemy auto-create (recommended for development)
-- Tables will be created automatically on next application start
-- if they don't exist

