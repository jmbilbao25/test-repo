package com.techstart.calculator;

import java.util.List;

/**
 * A record of every calculation the calculator has performed.
 *
 * <p>This is the second injected collaborator, and it exists so the tests have
 * an observable side effect to assert on. Without it every test could only
 * check a return value, and there would be nothing for {@code @AfterEach} to
 * clean up — which would make the lifecycle annotations look decorative rather
 * than necessary.
 */
public interface OperationLog {

    void record(Operation operation, double left, double right, double result);

    /** The entries so far, oldest first, as formatted strings. */
    List<String> entries();

    void clear();

    default int size() {
        return entries().size();
    }
}
