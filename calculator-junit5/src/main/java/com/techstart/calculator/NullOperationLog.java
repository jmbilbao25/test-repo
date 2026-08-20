package com.techstart.calculator;

import java.util.List;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Discards everything.
 *
 * <p>Used by the tests that are only interested in arithmetic, to show that
 * swapping one binding changes the calculator's behaviour without any change to
 * the calculator itself.
 */
@Singleton
public class NullOperationLog implements OperationLog {

    @Inject
    public NullOperationLog() {
    }

    @Override
    public void record(Operation operation, double left, double right, double result) {
        // deliberately nothing
    }

    @Override
    public List<String> entries() {
        return List.of();
    }

    @Override
    public void clear() {
        // nothing to clear
    }

    @Override
    public String toString() {
        return "NullOperationLog";
    }
}
