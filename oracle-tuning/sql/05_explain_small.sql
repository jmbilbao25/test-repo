-- Step 2: the execution plans while the table still holds the twelve rows the
-- assignment asked for.
--
-- The index from Step 1 exists and is visible. The point of this file is that
-- at this size the plans do not mean anything yet: the whole table is five
-- blocks, so the largest saving any index could win is a handful of block
-- reads. Q1 is full scanned and Q2 does use the index, and neither choice
-- matters. Step 2 has to make the table big enough for the question to have an
-- answer before it can claim to have optimised anything.

SET LINESIZE 150
SET PAGESIZE 300
SET SERVEROUTPUT OFF
SET FEEDBACK OFF

BEGIN
    DBMS_STATS.GATHER_TABLE_STATS('HR_DAY9', 'EMPLOYEES',
                                  cascade => TRUE);
    DBMS_STATS.GATHER_TABLE_STATS('HR_DAY9', 'DEPARTMENTS',
                                  cascade => TRUE);
END;
/

COLUMN table_name FORMAT A13
COLUMN num_rows FORMAT 999,999,999
PROMPT === how big the optimizer thinks the tables are ===
SELECT table_name, num_rows, blocks, avg_row_len
FROM   all_tables
WHERE  owner = 'HR_DAY9'
ORDER  BY table_name;

PROMPT
PROMPT === Q1: average salary per department, all twelve rows ===
SELECT /*+ GATHER_PLAN_STATISTICS q1_small */
       department_id, AVG(salary) AS avg_salary
FROM   hr_day9.employees
GROUP  BY department_id
ORDER  BY department_id;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

PROMPT
PROMPT === Q2: average salary for one department ===
SELECT /*+ GATHER_PLAN_STATISTICS q2_small */
       AVG(salary) AS avg_salary
FROM   hr_day9.employees
WHERE  department_id = 10;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));
