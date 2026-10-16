CREATE DATABASE support_ticket_db;
USE support_ticket_db;

UPDATE users
SET role = 'Admin'
WHERE email = 'testuser@example.com';

SELECT id, full_name, email, role
FROM users;


UPDATE users
SET role = 'Agent'
WHERE id = 4
  AND email = 'agent.three@example.com';

SELECT id, full_name, email, role
FROM users
WHERE id = 4;