package com.techstart.calculator;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * A calculator with the four basic arithmetic operations.
 *
 * <p>The class takes its two collaborators through the constructor and never
 * constructs one itself. That is the whole of the dependency injection design:
 * there is no static state, no service lookup and no {@code new} anywhere in
 * the class, so a test can supply whatever pair of implementations it needs and
 * the production wiring is just one more caller.
 *
 * <p>All four public operations funnel into {@link #apply}, so the validation
 * rules cannot be bypassed by picking a different method.
 */
@Singleton
public class Calculator {

    private final RoundingPolicy rounding;
    private final OperationLog log;

    @Inject
    public Calculator(RoundingPolicy rounding, OperationLog log) {
        if (rounding == null || log == null) {
            throw new IllegalArgumentException("calculator needs a rounding policy and a log");
        }
        this.rounding = rounding;
        this.log = log;
    }

    public double add(double left, double right) {
        return apply(Operation.ADD, left, right);
    }

    public double subtract(double left, double right) {
        return apply(Operation.SUBTRACT, left, right);
    }

    public double multiply(double left, double right) {
        return apply(Operation.MULTIPLY, left, right);
    }

    /**
     * @throws ArithmeticException if {@code right} is zero
     */
    public double divide(double left, double right) {
        return apply(Operation.DIVIDE, left, right);
    }

    /**
     * Runs one operation, with all the validation in front of it.
     *
     * @throws IllegalArgumentException if either operand is NaN or infinite
     * @throws ArithmeticException      on division by zero, or if the result
     *                                  overflows the range of a double
     */
    public double apply(Operation operation, double left, double right) {
        if (operation == null) {
            throw new IllegalArgumentException("operation is required");
        }
        requireFinite(left, "left operand");
        requireFinite(right, "right operand");

        // Integer division by zero throws, but floating point division by zero
        // does not: IEEE-754 defines 1.0/0.0 as positive infinity and 0.0/0.0
        // as NaN. Neither is an error as far as the JVM is concerned, so the
        // check has to be explicit or divide() would quietly return Infinity.
        if (operation == Operation.DIVIDE && right == 0.0) {
            throw new ArithmeticException(
                    "cannot divide " + trim(left) + " by zero");
        }

        double raw = operation.applyTo(left, right);
        if (!Double.isFinite(raw)) {
            throw new ArithmeticException("%s %s %s overflowed a double"
                    .formatted(trim(left), operation.symbol(), trim(right)));
        }

        double result = rounding.round(raw);
        log.record(operation, left, right, result);
        return result;
    }

    /** The operation history. Useful to callers, and asserted on by the tests. */
    public OperationLog history() {
        return log;
    }

    public RoundingPolicy roundingPolicy() {
        return rounding;
    }

    private static void requireFinite(double value, String what) {
        if (Double.isNaN(value)) {
            throw new IllegalArgumentException(what + " is not a number");
        }
        if (Double.isInfinite(value)) {
            throw new IllegalArgumentException(what + " is infinite");
        }
    }

    /**
     * Renders 4.0 as "4" for the message text.
     *
     * <p>The magnitude check matters: casting a double larger than
     * Long.MAX_VALUE to long saturates rather than overflowing, so without it
     * the overflow message for Double.MAX_VALUE would read 9223372036854775807.
     */
    private static String trim(double value) {
        if (Double.isFinite(value) && value == Math.rint(value)
                && Math.abs(value) < 1e15) {
            return String.valueOf((long) value);
        }
        return String.valueOf(value);
    }
}
