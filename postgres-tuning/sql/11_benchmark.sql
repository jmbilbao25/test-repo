-- A steadier measurement than a single EXPLAIN ANALYZE.
--
-- One run of a query that takes under a millisecond is mostly noise. This runs
-- each query 200 times and reports the mean that pg_stat_statements recorded,
-- which is stable enough to compare before and after an index.
SELECT pg_stat_statements_reset();

DO $$
BEGIN
    FOR i IN 1..200 LOOP
        PERFORM customer_id, amount, payment_date FROM payment
         WHERE payment_date >= '2007-02-15' AND payment_date < '2007-02-16';
        PERFORM payment_id, amount, payment_date FROM payment
         WHERE customer_id = 341 ORDER BY payment_date DESC LIMIT 10;
    END LOOP;
END $$;

\echo === mean execution time over 200 runs each ===
SELECT CASE WHEN query LIKE '%payment_date >=%' THEN 'Q1 (date range)'
            ELSE 'Q2 (customer, recent first)' END AS test_query,
       calls,
       round(mean_exec_time::numeric, 4) AS mean_ms,
       round(total_exec_time::numeric, 2) AS total_ms,
       round(shared_blks_hit::numeric / calls, 1) AS blocks_per_call
FROM pg_stat_statements
WHERE query LIKE 'SELECT %FROM payment%' AND calls = 200
ORDER BY test_query;
