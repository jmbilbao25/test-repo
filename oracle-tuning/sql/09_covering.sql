-- Step 2: the optimisation that does help Q1.
--
-- Q1 reads the whole table by definition, so no single-column index on
-- department_id can help it: whatever the optimizer used, it would still have
-- to visit every row. What it can be given instead is a narrower copy of the
-- table. An index on (department_id, salary) holds both columns Q1 needs, so
-- the aggregate can be satisfied from the index alone and the table never has
-- to be touched.

SET LINESIZE 150
SET PAGESIZE 300
SET FEEDBACK ON

PROMPT === a covering index for Q1 ===
CREATE INDEX hr_day9.employees_dept_sal_idx
    ON hr_day9.employees (department_id, salary);

SET FEEDBACK OFF

BEGIN
    DBMS_STATS.GATHER_TABLE_STATS(
        ownname       => 'HR_DAY9',
        tabname       => 'EMPLOYEES',
        method_opt    => 'FOR ALL COLUMNS SIZE 1 FOR COLUMNS SIZE 254 department_id',
        cascade       => TRUE,
        no_invalidate => FALSE);
END;
/

PROMPT
PROMPT === how much smaller the index is than the table ===
COLUMN segment_name FORMAT A26
COLUMN segment_type FORMAT A12
COLUMN mb FORMAT 990.99
SELECT segment_name, segment_type,
       ROUND(bytes / 1024 / 1024, 2) AS mb, blocks
FROM   dba_segments
WHERE  owner = 'HR_DAY9' AND segment_name IN
       ('EMPLOYEES', 'EMPLOYEES_DEPT_IDX', 'EMPLOYEES_DEPT_SAL_IDX')
ORDER  BY blocks DESC;

PROMPT
PROMPT === Q1 with the covering index available ===
-- A B-tree index skips a row only when every indexed column is NULL. salary is
-- NOT NULL, so this index has an entry for every employee, and the optimizer is
-- allowed to answer a GROUP BY over the whole table from it.
SELECT /*+ GATHER_PLAN_STATISTICS q1_covering */
       department_id, AVG(salary) AS avg_salary
FROM   hr_day9.employees
GROUP  BY department_id
ORDER  BY department_id;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

PROMPT
PROMPT === Q2 with the covering index available ===
SELECT /*+ GATHER_PLAN_STATISTICS q2_covering */
       AVG(salary) AS avg_salary
FROM   hr_day9.employees
WHERE  department_id = 10;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

PROMPT
PROMPT === which indexes the optimizer actually used ===
-- Index usage tracking is sampled, so this reports what was exercised rather
-- than proving a negative. It is here to confirm the plans above, not to
-- replace them.
COLUMN name FORMAT A26
COLUMN total_access_count FORMAT 999,999
SELECT name, total_access_count, total_exec_count, last_used
FROM   dba_index_usage
WHERE  owner = 'HR_DAY9'
ORDER  BY name;
