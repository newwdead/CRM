-- Add refresh token fields to users table
-- This migration adds support for JWT refresh tokens with token rotation

-- Add refresh_token_hash column (stores SHA256 hash of refresh token)
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_hash VARCHAR(255) NULL;

-- Add refresh_token_expires_at column (tracks token expiration)
ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_expires_at TIMESTAMP WITH TIME ZONE NULL;

-- Add last_refresh_at column (tracks last refresh time)
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_refresh_at TIMESTAMP WITH TIME ZONE NULL;

-- Create index on refresh_token_hash for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_refresh_token_hash ON users(refresh_token_hash);

-- Comment on columns for documentation
COMMENT ON COLUMN users.refresh_token_hash IS 'SHA256 hash of the current refresh token (for token rotation security)';
COMMENT ON COLUMN users.refresh_token_expires_at IS 'Expiration timestamp of the refresh token';
COMMENT ON COLUMN users.last_refresh_at IS 'Last time the user refreshed their access token';

