-- Step 3, prerequisite: put the database in ARCHIVELOG mode.
--
-- In NOARCHIVELOG mode the online redo logs are overwritten as they fill, so
-- the only thing RMAN can restore to is the moment the backup was taken, and
-- only from a backup taken while the database was shut down. ARCHIVELOG mode
-- copies each redo log off before it is reused, which is what makes both a
-- backup of an open database and a recovery to a chosen point in time possible.
-- The recovery in this assignment needs both.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK ON

PROMPT === before: the log mode as the image ships it ===
SELECT log_mode FROM v$database;

PROMPT
PROMPT === where the archived logs and backups will go ===
ALTER SYSTEM SET db_recovery_file_dest_size = 16G SCOPE=BOTH;
ALTER SYSTEM SET db_recovery_file_dest = '/opt/oracle/oradata/FRA' SCOPE=BOTH;

PROMPT
PROMPT === a clean bounce through MOUNT, which is where the switch is made ===
SHUTDOWN IMMEDIATE
STARTUP MOUNT
ALTER DATABASE ARCHIVELOG;
ALTER DATABASE OPEN;
ALTER PLUGGABLE DATABASE ALL OPEN;

SET FEEDBACK OFF
PROMPT
PROMPT === after ===
COLUMN name FORMAT A10
COLUMN log_mode FORMAT A13
COLUMN open_mode FORMAT A11
SELECT name, log_mode, open_mode FROM v$database;

PROMPT
COLUMN pdb_name FORMAT A14
SELECT con_id, name AS pdb_name, open_mode FROM v$pdbs ORDER BY con_id;

PROMPT
PROMPT === force a log switch so there is at least one archived log ===
ALTER SYSTEM ARCHIVE LOG CURRENT;

COLUMN status FORMAT A9
COLUMN first_time FORMAT A20
SELECT sequence#, TO_CHAR(first_time, 'YYYY-MM-DD HH24:MI:SS') AS first_time, status
FROM   v$archived_log
WHERE  standby_dest = 'NO'
ORDER  BY sequence#;

PROMPT
PROMPT === flash recovery area usage ===
COLUMN file_type FORMAT A22
COLUMN pct_used FORMAT 990.99
SELECT file_type, percent_space_used AS pct_used, number_of_files
FROM   v$flash_recovery_area_usage
WHERE  number_of_files > 0;
