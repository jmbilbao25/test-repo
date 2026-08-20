package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.stream.Stream;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.CsvFileSource;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * Step 3, first half: the same test body run against many inputs.
 *
 * <p>Each source below is here because it is the right tool for a different
 * job, not to list the API:
 *
 * <ul>
 *   <li>{@code @ValueSource} — one changing value, and the simplest thing that works.
 *   <li>{@code @CsvSource} — a few operands and an expected result, kept next to the test.
 *   <li>{@code @CsvFileSource} — the same table, in a file, so it can grow without
 *       the test class growing.
 *   <li>{@code @MethodSource} — cases that have to be computed rather than typed.
 *   <li>{@code @EnumSource} — every operation, and it cannot fall behind the enum.
 *   <li>{@code @NullAndEmptySource} — the two inputs everybody forgets.
 * </ul>
 *
 * <p>{@code @BeforeEach} runs before every generated case, not once for the
 * whole method, so each row still gets a clean calculator.
 */
@Tag("arithmetic")
@DisplayName("Calculator: parameterized")
class CalculatorParameterizedTest {

    /** Enough tolerance for binary floating point, tight enough to catch a real error. */
    private static final double TOLERANCE = 1e-9;

    private Calculator calculator;

    @BeforeEach
    void createCalculator() {
        calculator = new Calculator(new BankersRoundingPolicy(), new InMemoryOperationLog());
    }

    // -------------------------------------------------------------- ValueSource

    @ParameterizedTest(name = "{0} + 0 = {0}")
    @DisplayName("zero is the identity for addition")
    @ValueSource(doubles = {0.0, 1.0, -1.0, 2.5, -99.75, 1_000_000.0})
    void addingZeroChangesNothing(double value) {
        assertEquals(value, calculator.add(value, 0), TOLERANCE);
    }

    @ParameterizedTest(name = "{0} * 1 = {0}")
    @DisplayName("one is the identity for multiplication")
    @ValueSource(doubles = {0.0, 3.0, -7.5, 0.001})
    void multiplyingByOneChangesNothing(double value) {
        assertEquals(value, calculator.multiply(value, 1), TOLERANCE);
    }

    @ParameterizedTest(name = "{0} / 0 is refused")
    @DisplayName("no numerator makes division by zero acceptable")
    @ValueSource(doubles = {0.0, 1.0, -1.0, 1e10})
    void nothingMayBeDividedByZero(double numerator) {
        assertThrows(ArithmeticException.class, () -> calculator.divide(numerator, 0));
    }

    // ---------------------------------------------------------------- CsvSource

    @ParameterizedTest(name = "[{index}] {0} {1} {2} = {3}")
    @DisplayName("a table of cases written next to the test")
    @CsvSource({
            "4,    +, 5,   9",
            "-2.5, +, 2.5, 0",
            "10,   -, 3,   7",
            "3,    -, 10,  -7",
            "6,    *, 7,   42",
            "-4,   *, 2.5, -10",
            "9,    /, 4,   2.25",
            "-8,   /, 2,   -4",
    })
    void arithmeticFromCsv(double left, String symbol, double right, double expected) {
        assertEquals(expected, calculator.apply(Operation.fromSymbol(symbol), left, right),
                TOLERANCE);
    }

    // ------------------------------------------------------------ CsvFileSource

    @ParameterizedTest(name = "[{index}] {0} {1} {2} = {3}")
    @DisplayName("the same table, loaded from src/test/resources/operations.csv")
    @CsvFileSource(resources = "/operations.csv", numLinesToSkip = 1)
    void arithmeticFromCsvFile(double left, String symbol, double right, double expected) {
        assertEquals(expected, calculator.apply(Operation.fromSymbol(symbol), left, right),
                TOLERANCE);
    }

    // --------------------------------------------------------------- MethodSource

    /**
     * Cases that would be tedious to type: powers of two, checked against a
     * doubling that does not use the calculator.
     */
    static Stream<Arguments> doublingCases() {
        return Stream.iterate(1.0, value -> value * 2)
                .limit(12)
                .map(value -> Arguments.of(value, value + value));
    }

    @ParameterizedTest(name = "{0} * 2 = {1}")
    @DisplayName("generated cases, from a factory method")
    @MethodSource("doublingCases")
    void multiplyingByTwoIsAdditionToItself(double value, double expected) {
        assertEquals(expected, calculator.multiply(value, 2), TOLERANCE);
    }

    static Stream<Arguments> roundingCases() {
        // Ties, which is where HALF_EVEN and HALF_UP disagree. At scale 1:
        // 0.25 -> 0.2 (2 is even) and 0.35 -> 0.4 (4 is even). HALF_UP would
        // give 0.3 and 0.4.
        return Stream.of(
                Arguments.of(0.25, 0.2),
                Arguments.of(0.35, 0.4),
                Arguments.of(0.45, 0.4),
                Arguments.of(0.55, 0.6));
    }

    @ParameterizedTest(name = "{0} rounds to {1} at one decimal place")
    @DisplayName("banker's rounding sends a tie to the nearest even digit")
    @MethodSource("roundingCases")
    void banksRoundingBreaksTiesTowardsEven(double raw, double expected) {
        Calculator oneDecimalPlace = new Calculator(
                new BankersRoundingPolicy(1), new NullOperationLog());
        assertEquals(expected, oneDecimalPlace.add(raw, 0), TOLERANCE);
    }

    // ----------------------------------------------------------------- EnumSource

    @ParameterizedTest(name = "{0}")
    @DisplayName("every operation records exactly one history entry")
    @EnumSource(Operation.class)
    void everyOperationIsLogged(Operation operation) {
        // Whatever the operation, 6 and 3 are safe operands for it.
        calculator.apply(operation, 6, 3);
        assertEquals(1, calculator.history().size());
        assertTrue(calculator.history().entries().get(0).contains(operation.symbol()),
                () -> "expected the " + operation.symbol() + " symbol in "
                        + calculator.history().entries());
    }

    @ParameterizedTest(name = "{0} has a symbol that round-trips")
    @DisplayName("every symbol can be looked back up")
    @EnumSource(Operation.class)
    void symbolsRoundTrip(Operation operation) {
        assertEquals(operation, Operation.fromSymbol(operation.symbol()));
        // And with surrounding whitespace, which is what a parsed input has.
        assertEquals(operation, Operation.fromSymbol(" " + operation.symbol() + " "));
    }

    @ParameterizedTest(name = "{0} and {1} are not the same operation")
    @DisplayName("the two operations that are not commutative")
    @EnumSource(names = {"SUBTRACT", "DIVIDE"})
    void nonCommutativeOperations(Operation operation) {
        assertTrue(calculator.apply(operation, 10, 2)
                != calculator.apply(operation, 2, 10));
    }

    // --------------------------------------------------------- NullAndEmptySource

    @ParameterizedTest(name = "symbol [{0}] is refused")
    @DisplayName("null, empty and blank symbols are all refused")
    @NullAndEmptySource
    @ValueSource(strings = {" ", "\t", "^", "**", "plus", "++"})
    void unusableSymbols(String symbol) {
        // Stacking @NullAndEmptySource with @ValueSource is what makes null and
        // "" part of the same test as the merely wrong symbols. A @ValueSource
        // cannot express null on its own.
        assertThrows(IllegalArgumentException.class, () -> Operation.fromSymbol(symbol));
    }
}
