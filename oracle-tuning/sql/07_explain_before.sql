-- Step 2, the "before" plans, on 200,012 rows.
--
-- Rather than dropping the index to measure without it, it is made INVISIBLE.
-- Oracle keeps maintaining an invisible index but hides it from the optimizer,
-- so the before and after plans are taken against a byte-for-byte identical
-- table with identical statistics. Dropping and recreating would also change
-- the segment, and then the comparison would have two variables in it.

SET LINESIZE 150
SET PAGESIZE 300
SET FEEDBACK OFF

ALTER INDEX hr_day9.employees_dept_idx INVISIBLE;

COLUMN index_name FORMAT A24
COLUMN visibility FORMAT A10
PROMPT === the index is still there, and still maintained ===
SELECT index_name, status, visibility
FROM   all_indexes
WHERE  owner = 'HR_DAY9' AND index_name = 'EMPLOYEES_DEPT_IDX';

PROMPT
PROMPT === Q1 before: average salary per department, no usable index ===
SELECT /*+ GATHER_PLAN_STATISTICS q1_before */
       department_id, AVG(salary) AS avg_salary
FROM   hr_day9.employees
GROUP  BY department_id
ORDER  BY department_id;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

PROMPT
PROMPT === Q2 before: average salary for department 10, no usable index ===
SELECT /*+ GATHER_PLAN_STATISTICS q2_before */
       AVG(salary) AS avg_salary
FROM   hr_day9.employees
WHERE  department_id = 10;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));
