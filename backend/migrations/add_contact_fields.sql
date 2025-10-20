-- Migration: Add new fields to contacts table
-- Date: 2025-10-20
-- Description: Add name fields (first_name, last_name, middle_name), 
--              additional CRM fields, and timestamps

-- Add name fields
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_name VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS first_name VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS middle_name VARCHAR;

-- Add additional CRM fields
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS phone_mobile VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS phone_work VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS fax VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS department VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS birthday VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS source VARCHAR;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS priority VARCHAR;

-- Add timestamps
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Create index on company for faster grouping
CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at);

-- Update existing records: split full_name into components if possible
-- This is a basic split for Russian names (Фамилия Имя Отчество)
UPDATE contacts 
SET 
    last_name = COALESCE(SPLIT_PART(full_name, ' ', 1), ''),
    first_name = COALESCE(SPLIT_PART(full_name, ' ', 2), ''),
    middle_name = COALESCE(SPLIT_PART(full_name, ' ', 3), '')
WHERE full_name IS NOT NULL 
    AND last_name IS NULL 
    AND TRIM(full_name) != '';

COMMIT;

