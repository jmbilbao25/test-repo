-- Step 2, first half: the PL/SQL that reports the average salary per
-- department, as an anonymous block and then as a stored function other code
-- can call.

SET LINESIZE 130
SET PAGESIZE 200
SET SERVEROUTPUT ON SIZE UNLIMITED
SET FEEDBACK OFF

PROMPT === an anonymous PL/SQL block, one row per department ===

DECLARE
    -- The aggregate is left in SQL and the cursor walks the result. Averaging
    -- in PL/SQL instead would mean fetching every employee row across the
    -- call interface to compute a number the database can produce itself.
    CURSOR c_dept_avg IS
        SELECT   d.department_id,
                 d.department_name,
                 COUNT(e.employee_id)   AS headcount,
                 AVG(e.salary)          AS avg_salary
        FROM     hr_day9.departments d
                 LEFT JOIN hr_day9.employees e
                        ON e.department_id = d.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY d.department_id;

    l_reported PLS_INTEGER := 0;
BEGIN
    DBMS_OUTPUT.PUT_LINE(RPAD('DEPT', 6) || RPAD('DEPARTMENT', 24)
                         || LPAD('STAFF', 6) || LPAD('AVG SALARY', 14));
    DBMS_OUTPUT.PUT_LINE(RPAD('-', 50, '-'));

    FOR r IN c_dept_avg LOOP
        -- A department with no employees averages NULL rather than zero, and
        -- saying so is more honest than printing a 0.00 nobody earns.
        DBMS_OUTPUT.PUT_LINE(
            RPAD(r.department_id, 6)
            || RPAD(r.department_name, 24)
            || LPAD(r.headcount, 6)
            || LPAD(NVL(TO_CHAR(r.avg_salary, '9,999,999.99'), '     no staff'), 14));
        l_reported := l_reported + 1;
    END LOOP;

    DBMS_OUTPUT.PUT_LINE(RPAD('-', 50, '-'));
    DBMS_OUTPUT.PUT_LINE(l_reported || ' departments reported');
END;
/

PROMPT
PROMPT === the same thing as a stored function, so SQL can call it too ===

CREATE OR REPLACE FUNCTION hr_day9.dept_avg_salary (
    p_department_id IN hr_day9.departments.department_id%TYPE
) RETURN NUMBER
IS
    l_avg hr_day9.employees.salary%TYPE;
BEGIN
    SELECT AVG(salary)
    INTO   l_avg
    FROM   hr_day9.employees
    WHERE  department_id = p_department_id;

    RETURN ROUND(l_avg, 2);
EXCEPTION
    -- AVG over no rows returns NULL rather than raising, so NO_DATA_FOUND
    -- cannot happen here. An invalid department is still worth rejecting
    -- loudly instead of returning a NULL the caller may read as zero.
    WHEN OTHERS THEN
        RAISE_APPLICATION_ERROR(-20001,
            'cannot average department ' || p_department_id || ': ' || SQLERRM);
END dept_avg_salary;
/

SHOW ERRORS

COLUMN department_name FORMAT A24
COLUMN avg_salary FORMAT 999,999.99
SELECT d.department_id, d.department_name,
       hr_day9.dept_avg_salary(d.department_id) AS avg_salary
FROM   hr_day9.departments d
ORDER  BY d.department_id;
