-- Cleanup Test Data Script
-- Removes all test users and contacts from the database

-- Show what we're about to delete
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo 'Test Data Cleanup Script'
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
\echo ''

\echo '📋 Current counts:'
SELECT 'Users' as type, COUNT(*) as count FROM users
UNION ALL
SELECT 'Contacts', COUNT(*) FROM contacts;

\echo ''
\echo '🔍 Test users to be deleted:'
SELECT id, username, email, full_name FROM users 
WHERE username LIKE '%test%' 
   OR username LIKE '%Test%' 
   OR email LIKE '%test%' 
   OR full_name LIKE '%test%';

\echo ''
\echo '🔍 Test contacts to be deleted (sample):'
SELECT id, first_name, last_name, company, email FROM contacts 
WHERE company LIKE '%Test%' 
   OR company LIKE '%ABC%' 
   OR email LIKE '%test%' 
   OR email LIKE '%abc.com'
LIMIT 20;

\echo ''
\echo '⚠️  Deleting test data...'

-- Delete test users (but keep admin!)
DELETE FROM users 
WHERE (username LIKE '%test%' 
   OR username LIKE '%Test%' 
   OR email LIKE '%test%' 
   OR full_name LIKE '%test%')
  AND username != 'admin'
  AND is_admin = false;

-- Delete test contacts
DELETE FROM contacts 
WHERE company LIKE '%Test%' 
   OR company LIKE '%test%'
   OR company LIKE '%ABC%' 
   OR email LIKE '%test%' 
   OR email LIKE '%abc.com'
   OR email LIKE '%testcompany.com'
   OR first_name = 'a'
   OR last_name = 'a';

\echo ''
\echo '✅ Cleanup complete!'
\echo ''
\echo '📊 New counts:'
SELECT 'Users' as type, COUNT(*) as count FROM users
UNION ALL
SELECT 'Contacts', COUNT(*) FROM contacts;

\echo ''
\echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'

