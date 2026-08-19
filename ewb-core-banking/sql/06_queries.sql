-- Exercise 2, Step 2.3 -- filtering and aggregation.

\echo '--- Query A: accounts holding more than PHP 5,000.00 ---'
SELECT account_number, customer_name, balance
  FROM ewb_accounts
 WHERE balance > 5000.00;

\echo ''
\echo '--- Query B: total deposits EWB is holding across all accounts ---'
SELECT SUM(balance) AS total_ewb_deposits
  FROM ewb_accounts;

\echo ''
\echo '--- Query C: the same total, broken down by currency ---'
SELECT currency,
       count(*)     AS accounts,
       SUM(balance) AS total_balance
  FROM ewb_accounts
 GROUP BY currency
 ORDER BY currency;
