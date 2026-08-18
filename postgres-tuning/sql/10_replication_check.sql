-- Step 4: what the primary reports about its replica.
\echo === pg_stat_replication (run on the primary) ===
SELECT application_name,
       state,
       sync_state,
       sent_lsn,
       replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replay_lag_bytes
FROM pg_stat_replication;

\echo
\echo === replication slot ===
SELECT slot_name, slot_type, active FROM pg_replication_slots;
