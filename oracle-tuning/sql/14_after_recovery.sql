-- Step 3: what the database looks like once the recovery has finished.
--
-- Compare every number here with the same query in 12_before_backup.sql. The
-- row counts, the fingerprint and the object list all have to match, and the
-- departments row count has to match too: a recovery that brought the employees
-- back but rolled the rest of the schema somewhere else would not be a success.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK OFF

COLUMN name FORMAT A10
COLUMN log_mode FORMAT A13
COLUMN open_mode FORMAT A11
PROMPT === the database is open again ===
SELECT name, log_mode, open_mode FROM v$database;

PROMPT
COLUMN pdb_name FORMAT A14
SELECT con_id, name AS pdb_name, open_mode FROM v$pdbs ORDER BY con_id;

PROMPT
PROMPT === the employees table is back ===
COLUMN table_name FORMAT A14
COLUMN row_count FORMAT 999,999,999
COLUMN salary_total FORMAT 999,999,999,999.99
SELECT 'DEPARTMENTS' AS table_name, COUNT(*) AS row_count, NULL AS salary_total
FROM   hr_day9.departments
UNION ALL
SELECT 'EMPLOYEES', COUNT(*), SUM(salary) FROM hr_day9.employees;

PROMPT
PROMPT === and it is the same table, not just a table of the same size ===
COLUMN fingerprint FORMAT A20
SELECT TO_CHAR(SUM(ORA_HASH(employee_id || ':' || name || ':' ||
                            department_id || ':' || salary)))
       AS fingerprint
FROM   hr_day9.employees;

PROMPT
PROMPT === every object, including the two indexes and the function ===
COLUMN object_name FORMAT A26
COLUMN object_type FORMAT A12
SELECT object_name, object_type, status
FROM   all_objects
WHERE  owner = 'HR_DAY9'
ORDER  BY object_type, object_name;

PROMPT
PROMPT === the constraints came back with it ===
COLUMN constraint_name FORMAT A22
COLUMN c FORMAT A12
COLUMN table_name FORMAT A13
SELECT table_name, constraint_name,
       CASE constraint_type WHEN 'P' THEN 'PRIMARY KEY'
                            WHEN 'R' THEN 'FOREIGN KEY'
                            WHEN 'C' THEN 'CHECK' END AS c,
       status
FROM   all_constraints
WHERE  owner = 'HR_DAY9'
ORDER  BY table_name, constraint_type;

PROMPT
PROMPT === the stored function still runs ===
SET SERVEROUTPUT ON
COLUMN department_name FORMAT A24
COLUMN avg_salary FORMAT 999,999.99
SELECT d.department_id, d.department_name,
       hr_day9.dept_avg_salary(d.department_id) AS avg_salary
FROM   hr_day9.departments d
ORDER  BY d.department_id;

PROMPT
PROMPT === and the incarnation changed, which is the mark of a resetlogs ===
COLUMN status FORMAT A8
COLUMN resetlogs_time FORMAT A22
SELECT incarnation#, resetlogs_change#,
       TO_CHAR(resetlogs_time, 'YYYY-MM-DD HH24:MI:SS') AS resetlogs_time,
       status
FROM   v$database_incarnation
ORDER  BY incarnation#;
