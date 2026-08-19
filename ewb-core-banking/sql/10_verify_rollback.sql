-- Exercise 3, Step 3.2 -- verification that nothing partial survived.

\echo '--- Maria Clara, after the rejected transfer ---'
SELECT account_number, customer_name, balance
  FROM ewb_accounts
 WHERE account_number = 'EWB-1002';

\echo ''
\echo '--- both accounts, and the ledger row count: still 2 entries ---'
SELECT (SELECT SUM(balance) FROM ewb_accounts)     AS total_ewb_deposits,
       (SELECT count(*) FROM ewb_transactions)     AS ledger_entries;

\echo ''
\echo '--- customer ledger, joined back to the account master ---'
SELECT a.account_number,
       a.customer_name,
       t.transaction_type,
       t.amount,
       a.balance AS balance_now
  FROM ewb_accounts a
  JOIN ewb_transactions t ON t.account_number = a.account_number
 ORDER BY t.transaction_id;
