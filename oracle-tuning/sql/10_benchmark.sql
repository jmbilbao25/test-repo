-- Step 2: the plans say the indexes should help. This measures whether they do.
--
-- Each configuration gets its own comment tag, so each becomes a separate
-- cursor in the shared pool and v$sqlstats can report the logical reads for it
-- separately. Elapsed time is wall clock over the whole loop; buffer gets are
-- the number of blocks the database had to look at, which is the figure that
-- does not move around between runs.

SET LINESIZE 130
SET PAGESIZE 300
SET SERVEROUTPUT ON SIZE UNLIMITED
SET FEEDBACK OFF

DECLARE
    K_Q1_RUNS CONSTANT PLS_INTEGER := 50;
    K_Q2_RUNS CONSTANT PLS_INTEGER := 500;

    TYPE t_config IS RECORD (
        label     VARCHAR2(30),
        dept_idx  VARCHAR2(9),
        cover_idx VARCHAR2(9)
    );
    TYPE t_configs IS TABLE OF t_config;

    l_configs t_configs := t_configs(
        t_config('no index',       'INVISIBLE', 'INVISIBLE'),
        t_config('department_id',  'VISIBLE',   'INVISIBLE'),
        t_config('covering',       'VISIBLE',   'VISIBLE'));

    l_start  PLS_INTEGER;
    l_ms     NUMBER;
    l_dummy  NUMBER;
    l_tag    VARCHAR2(40);

    PROCEDURE report (p_label VARCHAR2, p_query VARCHAR2,
                      p_runs PLS_INTEGER, p_ms NUMBER, p_tag VARCHAR2)
    IS
        l_gets NUMBER;
        l_rows NUMBER;
    BEGIN
        SELECT SUM(buffer_gets) / GREATEST(SUM(executions), 1)
        INTO   l_gets
        FROM   v$sqlstats
        WHERE  sql_text LIKE '%' || p_tag || '%'
        AND    sql_text NOT LIKE '%v$sqlstats%';

        DBMS_OUTPUT.PUT_LINE(
            RPAD(p_query, 4) || RPAD(p_label, 16)
            || LPAD(TO_CHAR(p_runs, '9,999'), 7)
            || LPAD(TO_CHAR(p_ms / p_runs, '99,990.000'), 13)
            || LPAD(TO_CHAR(NVL(l_gets, 0), '9,999,990'), 13));
    END report;
BEGIN
    DBMS_OUTPUT.PUT_LINE(RPAD('Q', 4) || RPAD('INDEXES', 16)
                         || LPAD('RUNS', 7) || LPAD('MS / RUN', 13)
                         || LPAD('GETS / RUN', 13));
    DBMS_OUTPUT.PUT_LINE(RPAD('-', 53, '-'));

    FOR i IN 1 .. l_configs.COUNT LOOP
        EXECUTE IMMEDIATE 'ALTER INDEX hr_day9.employees_dept_idx '
                          || l_configs(i).dept_idx;
        EXECUTE IMMEDIATE 'ALTER INDEX hr_day9.employees_dept_sal_idx '
                          || l_configs(i).cover_idx;

        ------------------------------------------------------------ Q1
        l_tag := 'bench_q1_' || i;
        l_start := DBMS_UTILITY.GET_TIME;
        FOR r IN 1 .. K_Q1_RUNS LOOP
            EXECUTE IMMEDIATE
                'SELECT /* ' || l_tag || ' */ SUM(a) FROM ('
                || '  SELECT AVG(salary) a FROM hr_day9.employees'
                || '  GROUP BY department_id)'
            INTO l_dummy;
        END LOOP;
        l_ms := (DBMS_UTILITY.GET_TIME - l_start) * 10;
        report(l_configs(i).label, 'Q1', K_Q1_RUNS, l_ms, l_tag);

        ------------------------------------------------------------ Q2
        l_tag := 'bench_q2_' || i;
        l_start := DBMS_UTILITY.GET_TIME;
        FOR r IN 1 .. K_Q2_RUNS LOOP
            EXECUTE IMMEDIATE
                'SELECT /* ' || l_tag || ' */ AVG(salary)'
                || ' FROM hr_day9.employees WHERE department_id = 10'
            INTO l_dummy;
        END LOOP;
        l_ms := (DBMS_UTILITY.GET_TIME - l_start) * 10;
        report(l_configs(i).label, 'Q2', K_Q2_RUNS, l_ms, l_tag);
    END LOOP;

    DBMS_OUTPUT.PUT_LINE(RPAD('-', 53, '-'));
    DBMS_OUTPUT.PUT_LINE('Q1 = average salary per department (whole table)');
    DBMS_OUTPUT.PUT_LINE('Q2 = average salary for department 10 only');

    -- leave both indexes usable, which is the state the backup should capture
    EXECUTE IMMEDIATE 'ALTER INDEX hr_day9.employees_dept_idx VISIBLE';
    EXECUTE IMMEDIATE 'ALTER INDEX hr_day9.employees_dept_sal_idx VISIBLE';
END;
/
