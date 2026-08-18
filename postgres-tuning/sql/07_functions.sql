-- Step 3: a function and a procedure.
--
-- add_customer is a FUNCTION because the caller needs the generated
-- customer_id back. It validates before inserting, so a bad email or a
-- duplicate is rejected by the database rather than by whichever application
-- happens to be calling.
CREATE OR REPLACE FUNCTION add_customer(
        p_store_id   smallint,
        p_first_name text,
        p_last_name  text,
        p_email      text,
        p_address_id smallint)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_customer_id integer;
BEGIN
    IF p_email IS NULL OR position('@' IN p_email) = 0 THEN
        RAISE EXCEPTION 'not an email address: %', p_email
              USING ERRCODE = 'check_violation';
    END IF;

    IF EXISTS (SELECT 1 FROM customer WHERE lower(email) = lower(p_email)) THEN
        RAISE EXCEPTION 'email already registered: %', p_email
              USING ERRCODE = 'unique_violation';
    END IF;

    INSERT INTO customer (store_id, first_name, last_name, email,
                          address_id, activebool, create_date, active)
    VALUES (p_store_id, p_first_name, p_last_name, lower(p_email),
            p_address_id, true, current_date, 1)
    RETURNING customer_id INTO v_customer_id;

    RAISE NOTICE 'created customer % (%)', v_customer_id, lower(p_email);
    RETURN v_customer_id;
END;
$$;

-- deactivate_customer is a PROCEDURE. It returns nothing, and it commits its
-- own work: that transaction control is the thing a procedure can do and a
-- function cannot.
CREATE OR REPLACE PROCEDURE deactivate_customer(p_customer_id integer)
LANGUAGE plpgsql
AS $$
DECLARE
    v_rows integer;
BEGIN
    UPDATE customer
       SET activebool = false, active = 0, last_update = now()
     WHERE customer_id = p_customer_id AND activebool;

    GET DIAGNOSTICS v_rows = ROW_COUNT;

    IF v_rows = 0 THEN
        RAISE EXCEPTION 'no active customer with id %', p_customer_id
              USING ERRCODE = 'no_data_found';
    END IF;

    COMMIT;
    RAISE NOTICE 'customer % deactivated and committed', p_customer_id;
END;
$$;

\echo === what was created ===
SELECT p.proname AS name,
       CASE p.prokind WHEN 'f' THEN 'function' WHEN 'p' THEN 'procedure' END AS kind,
       pg_get_function_result(p.oid) AS returns
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname IN ('add_customer', 'deactivate_customer')
ORDER BY p.proname;
