package com.techstart.calculator;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Keeps the history in a list.
 *
 * <p>Bound as a singleton, which is exactly why the tests need an
 * {@code @AfterEach} that clears it: a singleton injected into a shared
 * injector carries state from one test into the next, and a test that depends
 * on the order it happens to run in is a test that will eventually fail for no
 * reason anybody can reproduce.
 */
@Singleton
public class InMemoryOperationLog implements OperationLog {

    private final List<String> entries = new ArrayList<>();

    @Inject
    public InMemoryOperationLog() {
    }

    @Override
    public void record(Operation operation, double left, double right, double result) {
        entries.add("%s %s %s = %s".formatted(
                format(left), operation.symbol(), format(right), format(result)));
    }

    @Override
    public List<String> entries() {
        return Collections.unmodifiableList(entries);
    }

    @Override
    public void clear() {
        entries.clear();
    }

    /**
     * Drops the trailing ".0" so the log reads 4 + 5 = 9 rather than 4.0 + 5.0 = 9.0.
     *
     * <p>Only for values a long can hold: the cast saturates rather than
     * overflowing, so 1e300 would otherwise be logged as Long.MAX_VALUE.
     */
    private static String format(double value) {
        if (Double.isFinite(value) && value == Math.rint(value)
                && Math.abs(value) < 1e15) {
            return String.valueOf((long) value);
        }
        return String.valueOf(value);
    }

    @Override
    public String toString() {
        return "InMemoryOperationLog(" + entries.size() + " entries)";
    }
}
