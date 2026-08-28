-- Step 2, the "after" plans: the same two queries with the Step 1 index
-- available to the optimizer again.

SET LINESIZE 150
SET PAGESIZE 300
SET FEEDBACK OFF

ALTER INDEX hr_day9.employees_dept_idx VISIBLE;

COLUMN index_name FORMAT A24
COLUMN visibility FORMAT A10
PROMPT === the index is visible to the optimizer again ===
SELECT index_name, status, visibility
FROM   all_indexes
WHERE  owner = 'HR_DAY9' AND index_name = 'EMPLOYEES_DEPT_IDX';

PROMPT
PROMPT === Q1 after: average salary per department, index available ===
SELECT /*+ GATHER_PLAN_STATISTICS q1_after */
       department_id, AVG(salary) AS avg_salary
FROM   hr_day9.employees
GROUP  BY department_id
ORDER  BY department_id;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

PROMPT
PROMPT === Q2 after: average salary for department 10, index available ===
SELECT /*+ GATHER_PLAN_STATISTICS q2_after */
       AVG(salary) AS avg_salary
FROM   hr_day9.employees
WHERE  department_id = 10;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

PROMPT
PROMPT === what it costs to force the index on Q1 anyway ===
-- The optimizer refused the index for Q1. This asks for it explicitly, so the
-- write-up can show what the plan it rejected would have cost.
SELECT /*+ GATHER_PLAN_STATISTICS INDEX(e employees_dept_idx) q1_forced */
       department_id, AVG(salary) AS avg_salary
FROM   hr_day9.employees e
GROUP  BY department_id
ORDER  BY department_id;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));
