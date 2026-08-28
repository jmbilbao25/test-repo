-- Step 3: exactly what the database holds at the moment the backup is taken,
-- so that the recovery at the end can be checked against something rather than
-- just declared successful. 14_after_recovery.sql runs the same queries again.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK OFF

COLUMN table_name FORMAT A14
COLUMN row_count FORMAT 999,999,999
COLUMN salary_total FORMAT 999,999,999,999.99
PROMPT === contents ===
SELECT 'DEPARTMENTS' AS table_name, COUNT(*) AS row_count, NULL AS salary_total
FROM   hr_day9.departments
UNION ALL
SELECT 'EMPLOYEES', COUNT(*), SUM(salary) FROM hr_day9.employees;

PROMPT
PROMPT === a fingerprint of the employees table ===
-- SUM over the salaries would not notice two rows swapping their values.
-- ORA_HASH over the ordered rows would notice, so it is a fair thing to compare
-- the recovered table against.
COLUMN fingerprint FORMAT A20
SELECT TO_CHAR(SUM(ORA_HASH(employee_id || ':' || name || ':' ||
                            department_id || ':' || salary)))
       AS fingerprint
FROM   hr_day9.employees;

PROMPT
PROMPT === the objects that must come back ===
COLUMN object_name FORMAT A26
COLUMN object_type FORMAT A12
SELECT object_name, object_type, status
FROM   all_objects
WHERE  owner = 'HR_DAY9'
ORDER  BY object_type, object_name;

PROMPT
PROMPT === the clock, for the record ===
COLUMN clock FORMAT A22
SELECT TO_CHAR(SYSTIMESTAMP, 'YYYY-MM-DD HH24:MI:SS') AS clock FROM dual;
