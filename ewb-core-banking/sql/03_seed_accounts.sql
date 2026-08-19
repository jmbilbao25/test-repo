-- Exercise 2, Step 2.1
-- The same two customers, this time with values the constraints accept.

INSERT INTO ewb_accounts (account_number, customer_name, balance)
VALUES
    ('EWB-1001', 'Juan Dela Cruz', 10000.00),
    ('EWB-1002', 'Maria Clara',     2500.00);

\echo ''
\echo '--- both accounts, with the columns the DEFAULTs filled in ---'
SELECT account_number, customer_name, currency, balance, status
  FROM ewb_accounts
 ORDER BY account_number;
