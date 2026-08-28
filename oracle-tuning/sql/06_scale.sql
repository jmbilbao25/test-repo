-- Step 2: give the optimizer a table where the choice of plan matters.
--
-- Twelve rows fit in one block, so no index can beat reading that block. This
-- adds 200,000 more employees, keeping the same ten departments and skewing the
-- distribution the way a real company is skewed: Executive stays tiny while the
-- operational departments hold tens of thousands of people.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK ON
SET TIMING ON

PROMPT === 200,000 more employees ===
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary)
SELECT 1000 + LEVEL,
       'Employee ' || TO_CHAR(1000 + LEVEL, 'FM000000'),
       -- every 400th row lands in Executive, so department 10 keeps roughly
       -- 500 people while the other nine hold about 24,900 each
       CASE WHEN MOD(LEVEL, 400) = 0 THEN 10
            ELSE 20 + 10 * MOD(LEVEL, 9) END,
       ROUND(30000 + DBMS_RANDOM.VALUE(0, 90000), 2)
FROM   dual
CONNECT BY LEVEL <= 200000;
COMMIT;

SET TIMING OFF
SET FEEDBACK OFF

PROMPT
PROMPT === restate the statistics, with a histogram on department_id ===
-- Without a histogram the optimizer assumes the ten departments are the same
-- size and costs a lookup on department 10 as one tenth of the table. The
-- histogram is what tells it department 10 is 0.25% of the table, and that is
-- the difference between an index range scan and a full scan.
BEGIN
    DBMS_STATS.GATHER_TABLE_STATS(
        ownname          => 'HR_DAY9',
        tabname          => 'EMPLOYEES',
        method_opt       => 'FOR ALL COLUMNS SIZE 1 FOR COLUMNS SIZE 254 department_id',
        cascade          => TRUE,
        no_invalidate    => FALSE);
END;
/

COLUMN table_name FORMAT A13
COLUMN num_rows FORMAT 999,999,999
SELECT table_name, num_rows, blocks, avg_row_len
FROM   all_tables
WHERE  owner = 'HR_DAY9'
ORDER  BY table_name;

PROMPT
PROMPT === the histogram Oracle built ===
COLUMN column_name FORMAT A15
COLUMN histogram FORMAT A12
SELECT column_name, num_distinct, num_buckets, histogram
FROM   all_tab_col_statistics
WHERE  owner = 'HR_DAY9' AND table_name = 'EMPLOYEES'
ORDER  BY column_name;

PROMPT
PROMPT === how the employees are spread across the departments ===
COLUMN department_name FORMAT A24
COLUMN headcount FORMAT 999,999
COLUMN pct FORMAT 990.99
COLUMN avg_salary FORMAT 999,999.99
SELECT   d.department_id, d.department_name,
         COUNT(e.employee_id) AS headcount,
         ROUND(RATIO_TO_REPORT(COUNT(e.employee_id)) OVER () * 100, 2) AS pct,
         ROUND(AVG(e.salary), 2) AS avg_salary
FROM     hr_day9.departments d
         LEFT JOIN hr_day9.employees e ON e.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY d.department_id;

PROMPT
PROMPT === segment sizes after the load ===
COLUMN segment_name FORMAT A22
COLUMN segment_type FORMAT A12
COLUMN mb FORMAT 990.99
SELECT segment_name, segment_type,
       ROUND(bytes / 1024 / 1024, 2) AS mb, blocks
FROM   dba_segments
WHERE  owner = 'HR_DAY9'
ORDER  BY segment_type, segment_name;
