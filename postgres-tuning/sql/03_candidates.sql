-- Step 2, first half: find the queries worth indexing instead of guessing.
--
-- pg_stat_statements records every statement the server has executed, with a
-- call count and total time. That is the evidence for "most frequently used".
\echo === busiest statements by total execution time ===
SELECT calls,
       round(total_exec_time::numeric, 2) AS total_ms,
       round(mean_exec_time::numeric, 3)  AS mean_ms,
       left(regexp_replace(query, '\s+', ' ', 'g'), 58) AS query
FROM pg_stat_statements
WHERE query LIKE '%payment%' AND query NOT LIKE '%pg_stat%'
ORDER BY total_exec_time DESC
LIMIT 5;

\echo
\echo === tables being read sequentially (a missing-index symptom) ===
SELECT relname,
       seq_scan,
       seq_tup_read,
       idx_scan,
       CASE WHEN seq_scan > 0
            THEN seq_tup_read / seq_scan END AS avg_rows_per_seq_scan
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 6;
