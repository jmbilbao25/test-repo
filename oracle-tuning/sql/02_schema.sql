-- Step 1, first half: the schema owner and the two tables the assignment asks
-- for, with twelve employees across ten departments.
--
-- Run as SYSDBA against FREEPDB1. The index is a separate file (03_index.sql)
-- so that the write-up can show the two operations apart.

SET LINESIZE 130
SET PAGESIZE 200
SET FEEDBACK ON

-- Nothing to drop on the first run, and there should not be a stack trace in
-- the screenshot for that.
SET FEEDBACK OFF
BEGIN
    EXECUTE IMMEDIATE 'DROP USER hr_day9 CASCADE';
EXCEPTION
    WHEN OTHERS THEN NULL;
END;
/
SET FEEDBACK ON

PROMPT === the schema owner ===
-- SELECT_CATALOG_ROLE is what lets HR_DAY9 read v$sql_plan through
-- DBMS_XPLAN.DISPLAY_CURSOR later on; the rest is an ordinary application user.
CREATE USER hr_day9 IDENTIFIED BY hr_day9_pw
  DEFAULT TABLESPACE users
  QUOTA UNLIMITED ON users;
GRANT CREATE SESSION, CREATE TABLE, CREATE PROCEDURE, CREATE VIEW TO hr_day9;
GRANT SELECT_CATALOG_ROLE TO hr_day9;

PROMPT
PROMPT === departments ===
-- departments is created first: employees.department_id references it, and a
-- foreign key cannot point at a table that does not exist yet.
CREATE TABLE hr_day9.departments (
    department_id   NUMBER(4)    NOT NULL,
    department_name VARCHAR2(40) NOT NULL,
    CONSTRAINT departments_pk PRIMARY KEY (department_id)
);

PROMPT
PROMPT === employees ===
CREATE TABLE hr_day9.employees (
    employee_id   NUMBER(8)     NOT NULL,
    name          VARCHAR2(60)  NOT NULL,
    department_id NUMBER(4),
    salary        NUMBER(10, 2) NOT NULL,
    CONSTRAINT employees_pk PRIMARY KEY (employee_id),
    CONSTRAINT employees_dept_fk FOREIGN KEY (department_id)
        REFERENCES hr_day9.departments (department_id),
    CONSTRAINT employees_salary_ck CHECK (salary > 0)
);

PROMPT
PROMPT === ten departments ===
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (10, 'Executive');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (20, 'Finance');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (30, 'Human Resources');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (40, 'Information Technology');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (50, 'Operations');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (60, 'Retail Banking');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (70, 'Treasury');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (80, 'Risk and Compliance');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (90, 'Internal Audit');
INSERT INTO hr_day9.departments (department_id, department_name) VALUES (100, 'Customer Service');

PROMPT
PROMPT === twelve employees ===
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (1, 'Amelia Reyes',     10,  185000.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (2, 'Bernard Cruz',     20,   96500.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (3, 'Corazon Vidal',    20,   88250.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (4, 'Diego Almonte',    30,   67400.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (5, 'Elena Marquez',    40,  112000.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (6, 'Fidel Ocampo',     40,  104750.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (7, 'Grace Bautista',   50,   73900.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (8, 'Hector Salcedo',   60,   58300.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (9, 'Imelda Fajardo',   70,  121600.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (10, 'Joaquin Tolentino', 80,  99800.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (11, 'Karina Delgado',  90,   84150.00);
INSERT INTO hr_day9.employees (employee_id, name, department_id, salary) VALUES (12, 'Lorenzo Pineda', 100,   61250.00);
COMMIT;

SET FEEDBACK OFF
PROMPT
PROMPT === what is in the two tables ===
COLUMN table_name FORMAT A14
COLUMN rows_loaded FORMAT 999,999
SELECT 'DEPARTMENTS' AS table_name, COUNT(*) AS rows_loaded FROM hr_day9.departments
UNION ALL
SELECT 'EMPLOYEES',   COUNT(*)                              FROM hr_day9.employees;

PROMPT
PROMPT === the employees, joined to their department ===
COLUMN name FORMAT A20
COLUMN department_name FORMAT A24
COLUMN salary FORMAT 999,999.99
SELECT e.employee_id, e.name, d.department_name, e.salary
FROM   hr_day9.employees e
       JOIN hr_day9.departments d ON d.department_id = e.department_id
ORDER  BY e.employee_id;

PROMPT
PROMPT === the constraints that came with them ===
COLUMN constraint_name FORMAT A22
COLUMN c FORMAT A12
COLUMN table_name FORMAT A13
COLUMN search_condition FORMAT A24
SELECT table_name, constraint_name,
       CASE constraint_type WHEN 'P' THEN 'PRIMARY KEY'
                            WHEN 'R' THEN 'FOREIGN KEY'
                            WHEN 'C' THEN 'CHECK'
                            WHEN 'U' THEN 'UNIQUE' END AS c,
       status
FROM   all_constraints
WHERE  owner = 'HR_DAY9'
ORDER  BY table_name, constraint_type, constraint_name;
