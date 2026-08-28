-- What the instance actually is, recorded before anything is built on it.
-- Everything after this runs against the FREEPDB1 pluggable database inside
-- this container database.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK OFF

COLUMN banner_full FORMAT A78
COLUMN host_name   FORMAT A16
COLUMN name        FORMAT A10
COLUMN open_mode   FORMAT A11
COLUMN log_mode    FORMAT A13
COLUMN pdb_name    FORMAT A14
COLUMN value       FORMAT A26
COLUMN parameter   FORMAT A26

PROMPT === version ===
SELECT banner_full FROM v$version;

PROMPT
PROMPT === the container database ===
SELECT name, cdb, open_mode, log_mode FROM v$database;

PROMPT
PROMPT === instance ===
SELECT instance_name, host_name, status, database_status FROM v$instance;

PROMPT
PROMPT === pluggable databases ===
SELECT con_id, name AS pdb_name, open_mode, restricted
FROM   v$pdbs
ORDER  BY con_id;

PROMPT
PROMPT === memory and file layout ===
SELECT name AS parameter, value
FROM   v$parameter
WHERE  name IN ('sga_target', 'pga_aggregate_target', 'db_block_size',
                'db_recovery_file_dest', 'db_recovery_file_dest_size',
                'undo_management', 'db_create_file_dest')
ORDER  BY name;
