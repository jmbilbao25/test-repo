-- Step 2: the two test queries, before any index exists.
\echo === Q1: payments taken on one day ===
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT customer_id, amount, payment_date
FROM payment
WHERE payment_date >= '2007-02-15' AND payment_date < '2007-02-16';

\echo
\echo === Q2: the ten most recent payments for one customer ===
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
SELECT payment_id, amount, payment_date
FROM payment
WHERE customer_id = 341
ORDER BY payment_date DESC
LIMIT 10;
