-- The tuning parameters, with the byte-based ones shown as sizes rather than as
-- a count of 8 kB blocks.
SELECT name,
       CASE unit
           WHEN '8kB' THEN pg_size_pretty(setting::bigint * 8192)
           WHEN 'kB'  THEN pg_size_pretty(setting::bigint * 1024)
           ELSE setting
       END AS value,
       source
FROM pg_settings
WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem',
               'maintenance_work_mem', 'random_page_cost')
ORDER BY name;
