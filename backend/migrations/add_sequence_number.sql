-- Migration: Add sequence_number to contacts table
-- Date: 2025-10-21
-- Description: Добавление порядкового номера контактов по мере добавления

-- Add sequence_number column
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS sequence_number INTEGER UNIQUE;

-- Create index for sequence_number
CREATE INDEX IF NOT EXISTS ix_contacts_sequence_number ON contacts(sequence_number);

-- Populate existing contacts with sequence numbers based on created_at
WITH numbered_contacts AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) as seq_num
    FROM contacts
)
UPDATE contacts
SET sequence_number = numbered_contacts.seq_num
FROM numbered_contacts
WHERE contacts.id = numbered_contacts.id AND contacts.sequence_number IS NULL;

-- Create function to auto-assign sequence_number
CREATE OR REPLACE FUNCTION assign_sequence_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.sequence_number IS NULL THEN
        SELECT COALESCE(MAX(sequence_number), 0) + 1 INTO NEW.sequence_number FROM contacts;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-assign sequence_number before insert
DROP TRIGGER IF EXISTS trigger_assign_sequence_number ON contacts;
CREATE TRIGGER trigger_assign_sequence_number
BEFORE INSERT ON contacts
FOR EACH ROW
EXECUTE FUNCTION assign_sequence_number();

