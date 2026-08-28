-- Step 1, second half: the index on employees.department_id.
--
-- Oracle already built a unique index behind each primary key, so this is the
-- third index in the schema rather than the first. It is also the only one that
-- is not free: the two primary key indexes exist whether we want them or not.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK ON

PROMPT === the index the assignment asks for ===
CREATE INDEX hr_day9.employees_dept_idx ON hr_day9.employees (department_id);

SET FEEDBACK OFF
PROMPT
PROMPT === every index on the two tables now ===
COLUMN table_name  FORMAT A13
COLUMN index_name  FORMAT A22
COLUMN uniqueness  FORMAT A10
COLUMN columns     FORMAT A24
COLUMN index_type  FORMAT A10
SELECT i.table_name, i.index_name, i.index_type, i.uniqueness,
       (SELECT LISTAGG(c.column_name, ', ')
                 WITHIN GROUP (ORDER BY c.column_position)
         FROM   all_ind_columns c
         WHERE  c.index_owner = i.owner AND c.index_name = i.index_name)
       AS columns
FROM   all_indexes i
WHERE  i.owner = 'HR_DAY9'
ORDER  BY i.table_name, i.index_name;

PROMPT
PROMPT === and what each one costs on disk ===
COLUMN segment_name FORMAT A22
COLUMN segment_type FORMAT A12
COLUMN kb FORMAT 999,999
SELECT segment_name, segment_type, bytes / 1024 AS kb, blocks
FROM   dba_segments
WHERE  owner = 'HR_DAY9'
ORDER  BY segment_type, segment_name;
