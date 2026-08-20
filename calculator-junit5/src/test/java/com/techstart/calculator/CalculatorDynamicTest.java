package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.DynamicContainer.dynamicContainer;
import static org.junit.jupiter.api.DynamicTest.dynamicTest;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.DynamicNode;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.TestFactory;

/**
 * Step 4: dynamic tests, generated at run time by a {@code @TestFactory}.
 *
 * <p>The difference from {@code @ParameterizedTest} is when the cases are
 * decided. A parameterized test's cases are fixed at compile time by its
 * annotation. A factory's cases are whatever the code returns while the test is
 * running, so the set can depend on a file that was read, a value that was
 * computed, or another test's outcome.
 *
 * <p>The cost is real: a dynamic test has no lifecycle. {@code @BeforeEach} and
 * {@code @AfterEach} run once around the whole factory, not around each
 * generated case, so anything a case needs has to be built inside its own
 * executable. Every factory below constructs its own calculator for that reason.
 */
@Tag("arithmetic")
@DisplayName("Calculator: dynamic tests")
class CalculatorDynamicTest {

    private static final double TOLERANCE = 1e-9;

    private static Calculator freshCalculator() {
        return new Calculator(new BankersRoundingPolicy(), new InMemoryOperationLog());
    }

    /**
     * One test per row of the CSV, named after the row.
     *
     * <p>The file is the same one {@code @CsvFileSource} reads. Here it is
     * parsed by hand, which is the point: adding a row to the file adds a test
     * without anybody touching this class, and the count in the report goes up.
     */
    @TestFactory
    @DisplayName("one test per row of operations.csv")
    Stream<DynamicTest> casesFromTheCsvFile() {
        return readCsvRows().stream().map(row -> dynamicTest(
                "%s %s %s = %s".formatted(row[0], row[1], row[2], row[3]),
                () -> {
                    Calculator calculator = freshCalculator();
                    double result = calculator.apply(Operation.fromSymbol(row[1]),
                            Double.parseDouble(row[0]), Double.parseDouble(row[2]));
                    assertEquals(Double.parseDouble(row[3]), result, TOLERANCE);
                }));
    }

    /**
     * Every operation crossed with every operand pair, grouped per operation.
     *
     * <p>{@code dynamicContainer} gives the report a tree rather than a flat
     * list, so a failure is reported as DIVIDE / 7 and 0 rather than as case 23.
     * Four operations and six pairs generate twenty-four tests from one method.
     */
    @TestFactory
    @DisplayName("every operation against every operand pair")
    Stream<DynamicNode> everyOperationAgainstEveryPair() {
        double[][] pairs = {{6, 3}, {-6, 3}, {2.5, 0.5}, {0, 5}, {7, 0}, {1e6, 1e-6}};

        return Stream.of(Operation.values()).map(operation -> dynamicContainer(
                operation.name(),
                Stream.of(pairs).map(pair -> dynamicTest(
                        "%s %s %s".formatted(trim(pair[0]), operation.symbol(), trim(pair[1])),
                        () -> checkOneCase(operation, pair[0], pair[1])))));
    }

    /**
     * The invariant, not the answer: whatever the operation does, the calculator
     * either returns a finite number and logs it once, or refuses and logs
     * nothing. Division by zero is the only case here that must refuse.
     */
    private void checkOneCase(Operation operation, double left, double right) {
        Calculator calculator = freshCalculator();
        boolean mustRefuse = operation == Operation.DIVIDE && right == 0.0;

        if (mustRefuse) {
            assertThrows(ArithmeticException.class,
                    () -> calculator.apply(operation, left, right));
            assertEquals(0, calculator.history().size(),
                    "a refused operation must not be logged");
            return;
        }

        double result = calculator.apply(operation, left, right);
        assertTrue(Double.isFinite(result), () -> "not finite: " + result);
        assertEquals(1, calculator.history().size());
        assertEquals(result, operation.applyTo(left, right), 1e-6,
                "the calculator should agree with the raw operation");
    }

    /**
     * Cases the factory works out for itself: the largest power of ten the
     * calculator can still square without overflowing.
     *
     * <p>This is the kind of test set that cannot be written as an annotation,
     * because the boundary is not known until it has been searched for.
     */
    @TestFactory
    @DisplayName("squaring, up to the overflow boundary that is found at run time")
    Stream<DynamicTest> squaringUpToTheOverflowBoundary() {
        int highestSafeExponent = 0;
        Calculator probe = freshCalculator();
        for (int exponent = 0; exponent <= 400; exponent++) {
            try {
                double value = Math.pow(10, exponent);
                probe.multiply(value, value);
                highestSafeExponent = exponent;
            } catch (ArithmeticException overflow) {
                break;
            }
        }

        List<DynamicTest> tests = new ArrayList<>();
        int boundary = highestSafeExponent;

        // A handful of exponents below the boundary must succeed.
        for (int exponent : new int[]{0, 1, 10, boundary / 2, boundary}) {
            double value = Math.pow(10, exponent);
            tests.add(dynamicTest("10^" + exponent + " squared is representable",
                    () -> assertTrue(Double.isFinite(freshCalculator().multiply(value, value)))));
        }

        // And the first one past it must be refused.
        double past = Math.pow(10, boundary + 1);
        tests.add(dynamicTest("10^" + (boundary + 1) + " squared overflows", () -> {
            ArithmeticException thrown = assertThrows(ArithmeticException.class,
                    () -> freshCalculator().multiply(past, past));
            assertTrue(thrown.getMessage().endsWith("overflowed a double"));
        }));

        return tests.stream();
    }

    // ------------------------------------------------------------------ helpers

    /** The CSV rows, without the header, split on commas and trimmed. */
    private static List<String[]> readCsvRows() {
        try (InputStream in =
                     CalculatorDynamicTest.class.getResourceAsStream("/operations.csv")) {
            if (in == null) {
                throw new IllegalStateException("operations.csv is not on the test classpath");
            }
            String text = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            return text.lines()
                    .skip(1)
                    .filter(line -> !line.isBlank())
                    .map(line -> Stream.of(line.split(",")).map(String::strip).toArray(String[]::new))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            throw new UncheckedIOException("could not read operations.csv", e);
        }
    }

    private static String trim(double value) {
        if (Double.isFinite(value) && value == Math.rint(value) && Math.abs(value) < 1e15) {
            return String.valueOf((long) value);
        }
        return String.valueOf(value);
    }
}
