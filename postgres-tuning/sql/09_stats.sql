-- Step 5: the two monitoring views the assignment asks for.
\echo === pg_stat_user_tables: sequential vs index reads ===
SELECT relname,
       seq_scan, seq_tup_read, idx_scan, n_live_tup
FROM pg_stat_user_tables
WHERE relname IN ('payment', 'rental', 'customer', 'film')
ORDER BY relname;

\echo
\echo === pg_stat_user_indexes: is each index actually being used? ===
SELECT indexrelname AS index_name,
       idx_scan AS scans,
       idx_tup_read AS tuples_read,
       pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE relname = 'payment'
ORDER BY idx_scan DESC, indexrelname;

\echo
\echo === cache hit ratio (how often a read was served from shared_buffers) ===
SELECT relname,
       heap_blks_read AS disk_blocks,
       heap_blks_hit  AS cache_blocks,
       round(100.0 * heap_blks_hit
             / nullif(heap_blks_hit + heap_blks_read, 0), 2) AS cache_hit_pct
FROM pg_statio_user_tables
WHERE relname IN ('payment', 'rental', 'customer', 'film')
ORDER BY relname;
