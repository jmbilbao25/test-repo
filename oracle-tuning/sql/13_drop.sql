-- Step 3: the simulated failure.
--
-- PURGE is deliberate. A plain DROP TABLE moves the segment to the recycle bin,
-- and then "recovery" is one FLASHBACK TABLE ... TO BEFORE DROP away and the
-- backup is never touched. PURGE removes that shortcut, which is the whole
-- point: the assignment asks for a recovery from the backup, so the failure has
-- to be one the backup is the only answer to.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK OFF

PROMPT === the point the recovery will aim for, read one statement before ===
PROMPT === the damage is done                                            ===
-- The SCN is the database's own logical clock: every commit gets a higher one.
-- "Recover until this SCN" therefore means "put the database back the way it was
-- on this line of this file". setup.sh reads this number straight out of the
-- captured output and hands it to RMAN, so the number in the recovery command is
-- this number and not a retyped copy of it.
COLUMN restore_point FORMAT A40
SELECT 'RESTORE_POINT_SCN=' || TO_CHAR(current_scn) AS restore_point
FROM   v$database;

PROMPT
PROMPT === the failure ===
SET FEEDBACK ON
DROP TABLE hr_day9.employees CASCADE CONSTRAINTS PURGE;

SET FEEDBACK OFF
PROMPT
PROMPT === it is gone ===
COLUMN object_name FORMAT A26
COLUMN object_type FORMAT A12
SELECT object_name, object_type, status
FROM   all_objects
WHERE  owner = 'HR_DAY9'
ORDER  BY object_type, object_name;

PROMPT
PROMPT === nothing in the recycle bin to flash back to ===
COLUMN original_name FORMAT A20
COLUMN droptime FORMAT A20
SELECT owner, original_name, type, droptime
FROM   dba_recyclebin
WHERE  owner = 'HR_DAY9';

PROMPT
PROMPT === so the two obvious shortcuts both fail ===
SET FEEDBACK ON
FLASHBACK TABLE hr_day9.employees TO BEFORE DROP;
SELECT COUNT(*) FROM hr_day9.employees;

PROMPT
PROMPT === and the index went with the table ===
SET FEEDBACK OFF
COLUMN index_name FORMAT A22
COLUMN table_name FORMAT A14
SELECT index_name, table_name, status
FROM   all_indexes
WHERE  owner = 'HR_DAY9';

PROMPT
PROMPT === the departments table is untouched, which is what makes this a ===
PROMPT === partial loss rather than a lost database                       ===
SELECT COUNT(*) AS departments FROM hr_day9.departments;
