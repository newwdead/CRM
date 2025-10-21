-- Migration: Create duplicate_contacts table
-- Date: 2025-10-21
-- Description: Таблица для хранения найденных дубликатов контактов

-- Create duplicate_contacts table
CREATE TABLE IF NOT EXISTS duplicate_contacts (
    id SERIAL PRIMARY KEY,
    contact_id_1 INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    contact_id_2 INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,  -- 0.0 to 1.0
    match_fields JSONB,  -- {"name": 0.95, "email": 1.0, "phone": 0.85}
    status VARCHAR(20) DEFAULT 'pending',  -- pending, reviewed, merged, ignored
    auto_detected BOOLEAN DEFAULT false,  -- Найден автоматически или вручную
    detected_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id),
    merged_into INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    
    -- Ensure we don't store duplicate pairs
    CONSTRAINT unique_duplicate_pair UNIQUE (contact_id_1, contact_id_2),
    -- Ensure contact_id_1 < contact_id_2 (avoid (1,2) and (2,1))
    CONSTRAINT check_contact_order CHECK (contact_id_1 < contact_id_2)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_duplicate_contact_id_1 ON duplicate_contacts(contact_id_1);
CREATE INDEX IF NOT EXISTS idx_duplicate_contact_id_2 ON duplicate_contacts(contact_id_2);
CREATE INDEX IF NOT EXISTS idx_duplicate_status ON duplicate_contacts(status);
CREATE INDEX IF NOT EXISTS idx_duplicate_similarity ON duplicate_contacts(similarity_score DESC);

-- Function to ensure contact_id_1 < contact_id_2
CREATE OR REPLACE FUNCTION ensure_contact_order()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.contact_id_1 > NEW.contact_id_2 THEN
        -- Swap if in wrong order
        DECLARE
            temp INTEGER;
        BEGIN
            temp := NEW.contact_id_1;
            NEW.contact_id_1 := NEW.contact_id_2;
            NEW.contact_id_2 := temp;
        END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce contact order
DROP TRIGGER IF EXISTS trigger_ensure_contact_order ON duplicate_contacts;
CREATE TRIGGER trigger_ensure_contact_order
BEFORE INSERT OR UPDATE ON duplicate_contacts
FOR EACH ROW
EXECUTE FUNCTION ensure_contact_order();

-- Create system settings for duplicate detection if not exists
INSERT INTO system_settings (key, value, description, category)
VALUES 
    ('duplicate_detection_enabled', 'true', 'Enable automatic duplicate detection', 'duplicates'),
    ('duplicate_similarity_threshold', '0.75', 'Minimum similarity score to mark as duplicate (0.0-1.0)', 'duplicates'),
    ('duplicate_check_frequency_hours', '24', 'How often to run automatic duplicate check (hours)', 'duplicates'),
    ('duplicate_check_new_only', 'true', 'Only check newly created contacts for duplicates', 'duplicates')
ON CONFLICT (key) DO NOTHING;

-- Create view for easy duplicate lookup
CREATE OR REPLACE VIEW duplicate_contacts_view AS
SELECT 
    dc.id,
    dc.contact_id_1,
    dc.contact_id_2,
    c1.full_name as contact_1_name,
    c1.company as contact_1_company,
    c1.email as contact_1_email,
    c1.phone as contact_1_phone,
    c2.full_name as contact_2_name,
    c2.company as contact_2_company,
    c2.email as contact_2_email,
    c2.phone as contact_2_phone,
    dc.similarity_score,
    dc.match_fields,
    dc.status,
    dc.auto_detected,
    dc.detected_at,
    dc.reviewed_at,
    u.username as reviewed_by_username
FROM duplicate_contacts dc
JOIN contacts c1 ON dc.contact_id_1 = c1.id
JOIN contacts c2 ON dc.contact_id_2 = c2.id
LEFT JOIN users u ON dc.reviewed_by = u.id
ORDER BY dc.similarity_score DESC, dc.detected_at DESC;

COMMENT ON TABLE duplicate_contacts IS 'Stores detected duplicate contacts for review and merging';
COMMENT ON COLUMN duplicate_contacts.similarity_score IS 'Overall similarity score between 0.0 and 1.0';
COMMENT ON COLUMN duplicate_contacts.match_fields IS 'JSON object with similarity scores for each field';
COMMENT ON COLUMN duplicate_contacts.status IS 'pending: awaiting review, reviewed: marked by user, merged: contacts merged, ignored: marked as not duplicate';

