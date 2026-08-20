package com.techstart.calculator;

import java.util.function.DoubleBinaryOperator;

/**
 * The four arithmetic operations, each paired with its symbol and the raw
 * calculation.
 *
 * <p>The enum deliberately holds nothing but the pure arithmetic. Validation
 * (division by zero, non-finite inputs, overflow) lives in {@link Calculator},
 * so there is exactly one place where the rules are enforced no matter which
 * entry point is used.
 *
 * <p>Being an enum makes the whole operation set available to a test without
 * the test restating it, which is what {@code @EnumSource} and the dynamic
 * tests rely on.
 */
public enum Operation {

    ADD("+", (a, b) -> a + b),
    SUBTRACT("-", (a, b) -> a - b),
    MULTIPLY("*", (a, b) -> a * b),
    DIVIDE("/", (a, b) -> a / b);

    private final String symbol;
    private final DoubleBinaryOperator arithmetic;

    Operation(String symbol, DoubleBinaryOperator arithmetic) {
        this.symbol = symbol;
        this.arithmetic = arithmetic;
    }

    public String symbol() {
        return symbol;
    }

    /**
     * The raw IEEE-754 result, with no validation at all. Dividing by zero
     * here returns {@code Infinity} rather than throwing; that is the whole
     * reason {@link Calculator} has to check first.
     */
    public double applyTo(double left, double right) {
        return arithmetic.applyAsDouble(left, right);
    }

    /**
     * Looks an operation up by its symbol.
     *
     * @throws IllegalArgumentException if the symbol is null, blank or unknown
     */
    public static Operation fromSymbol(String symbol) {
        if (symbol == null || symbol.isBlank()) {
            throw new IllegalArgumentException("operation symbol is required");
        }
        String wanted = symbol.strip();
        for (Operation operation : values()) {
            if (operation.symbol.equals(wanted)) {
                return operation;
            }
        }
        throw new IllegalArgumentException("unknown operation: " + symbol);
    }
}
