-- Exercise 1, Step 1.2 -- intentional failures.
--
-- Every statement in this file is supposed to be rejected. ON_ERROR_STOP is
-- deliberately left off when this file is run, so psql reports each error and
-- carries on to the next attempt instead of aborting at the first one.

\echo '--- Attempt A: negative opening balance ---'
INSERT INTO ewb_accounts (account_number, customer_name, balance)
VALUES ('EWB-1001', 'Juan Dela Cruz', -500.00);
-- EXPECTED: violates check constraint "check_positive_balance"

\echo ''
\echo '--- Attempt B: unapproved currency (EUR) ---'
INSERT INTO ewb_accounts (account_number, customer_name, currency, balance)
VALUES ('EWB-1002', 'Maria Clara', 'EUR', 1000.00);
-- EXPECTED: violates check constraint "check_valid_currency"

\echo ''
\echo '--- the table is still empty: nothing bad got through ---'
SELECT count(*) AS rows_in_ewb_accounts FROM ewb_accounts;
