-- Exercise 3, Step 3.1 -- verification.

\echo '--- balances after the commit ---'
SELECT account_number, customer_name, balance
  FROM ewb_accounts
 ORDER BY account_number;

\echo ''
\echo '--- the ledger the transfer wrote ---'
SELECT transaction_id, account_number, transaction_type, amount, created_at
  FROM ewb_transactions
 ORDER BY transaction_id;

\echo ''
\echo '--- double entry check: DEBIT total must equal CREDIT total ---'
SELECT SUM(amount) FILTER (WHERE transaction_type = 'DEBIT')  AS total_debits,
       SUM(amount) FILTER (WHERE transaction_type = 'CREDIT') AS total_credits,
       SUM(CASE WHEN transaction_type = 'DEBIT'  THEN -amount
                WHEN transaction_type = 'CREDIT' THEN  amount END) AS net
  FROM ewb_transactions;

\echo ''
\echo '--- total deposits held: unchanged by an internal transfer ---'
SELECT SUM(balance) AS total_ewb_deposits FROM ewb_accounts;
