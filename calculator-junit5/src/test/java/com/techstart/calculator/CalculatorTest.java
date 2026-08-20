package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/**
 * Step 2: the lifecycle annotations and the two assertions the assignment asks
 * for, applied to the four operations.
 *
 * <p>The fixture is rebuilt in {@code @BeforeEach} rather than in a field
 * initialiser, and the log is cleared in {@code @AfterEach}. Both matter,
 * because {@code InMemoryOperationLog} is stateful: a calculator shared between
 * tests would let the order the tests happen to run in change the result.
 */
@Tag("arithmetic")
@DisplayName("Calculator: the four arithmetic operations")
class CalculatorTest {

    /** Static, so it survives between the per-method instances of this class. */
    private static int testsStarted;

    private Calculator calculator;
    private InMemoryOperationLog log;

    @BeforeAll
    static void beforeAll() {
        // Runs once, before any instance of this class exists, which is why it
        // has to be static and cannot touch the fixture fields.
        testsStarted = 0;
    }

    @BeforeEach
    void createCalculator() {
        log = new InMemoryOperationLog();
        calculator = new Calculator(new BankersRoundingPolicy(), log);
        testsStarted++;
    }

    @AfterEach
    void clearHistory() {
        // Cleaning up here rather than at the top of the next test means a test
        // that fails halfway through still leaves nothing behind.
        log.clear();
        assertEquals(0, log.size(), "the log should be empty for the next test");
    }

    @AfterAll
    static void afterAll() {
        assertTrue(testsStarted > 0, "@BeforeEach should have run at least once");
    }

    // ------------------------------------------------------------ the four ops

    @Test
    @DisplayName("addition: 4 + 5 = 9")
    void adds() {
        assertEquals(9.0, calculator.add(4, 5));
    }

    @Test
    @DisplayName("subtraction: 10 - 3 = 7, and it is not commutative")
    void subtracts() {
        assertEquals(7.0, calculator.subtract(10, 3));
        assertEquals(-7.0, calculator.subtract(3, 10));
    }

    @Test
    @DisplayName("multiplication: 6 * 7 = 42, including a negative operand")
    void multiplies() {
        assertEquals(42.0, calculator.multiply(6, 7));
        assertEquals(-10.0, calculator.multiply(-4, 2.5));
    }

    @Test
    @DisplayName("division: 9 / 4 = 2.25")
    void divides() {
        assertEquals(2.25, calculator.divide(9, 4));
    }

    @Test
    @DisplayName("all four at once, so one failure does not hide the rest")
    void allFourOperations() {
        // assertAll evaluates every executable even after one has failed, and
        // reports them together. Four separate assertEquals calls would stop at
        // the first, which turns fixing a broken calculator into four runs.
        assertAll("the four operations",
                () -> assertEquals(9.0, calculator.add(4, 5), "add"),
                () -> assertEquals(7.0, calculator.subtract(10, 3), "subtract"),
                () -> assertEquals(42.0, calculator.multiply(6, 7), "multiply"),
                () -> assertEquals(2.25, calculator.divide(9, 4), "divide"));
    }

    // ------------------------------------------------------------- refusals

    @Test
    @DisplayName("dividing by zero throws ArithmeticException")
    void divideByZeroThrows() {
        // The lambda is the important part: assertThrows needs the call to
        // happen inside it, otherwise the exception escapes before the
        // assertion can catch it.
        ArithmeticException thrown = assertThrows(ArithmeticException.class,
                () -> calculator.divide(1, 0));

        // Asserting on the message as well. A test that only checks the type
        // would still pass if the calculator threw for some unrelated reason.
        assertEquals("cannot divide 1 by zero", thrown.getMessage());
    }

    @Test
    @DisplayName("0 / 0 is refused too, rather than returning NaN")
    void zeroDividedByZeroThrows() {
        assertThrows(ArithmeticException.class, () -> calculator.divide(0, 0));
    }

    @Test
    @DisplayName("NaN and infinite operands are rejected before any arithmetic")
    void rejectsNonFiniteOperands() {
        assertAll(
                () -> assertEquals("left operand is not a number",
                        assertThrows(IllegalArgumentException.class,
                                () -> calculator.add(Double.NaN, 1)).getMessage()),
                () -> assertEquals("right operand is infinite",
                        assertThrows(IllegalArgumentException.class,
                                () -> calculator.add(1, Double.POSITIVE_INFINITY)).getMessage()));
        assertEquals(0, log.size(), "a rejected call should not be logged");
    }

    @Test
    @DisplayName("a result too large for a double is an error, not Infinity")
    void overflowThrows() {
        ArithmeticException thrown = assertThrows(ArithmeticException.class,
                () -> calculator.multiply(Double.MAX_VALUE, 2));
        assertTrue(thrown.getMessage().endsWith("overflowed a double"),
                () -> "unexpected message: " + thrown.getMessage());
    }

    @Test
    @DisplayName("assertThrowsExactly rejects a subclass; assertThrows accepts one")
    void exactExceptionType() {
        // ArithmeticException extends RuntimeException. assertThrows would be
        // satisfied by RuntimeException.class, which is a weaker statement than
        // this test wants to make.
        assertThrows(RuntimeException.class, () -> calculator.divide(1, 0));
        assertThrowsExactly(ArithmeticException.class, () -> calculator.divide(1, 0));
    }

    @Test
    @DisplayName("the constructor refuses to build a calculator with no collaborators")
    void constructorRequiresCollaborators() {
        assertThrows(IllegalArgumentException.class,
                () -> new Calculator(null, log));
        assertThrows(IllegalArgumentException.class,
                () -> new Calculator(new BankersRoundingPolicy(), null));
    }

    // ------------------------------------------------------- the injected log

    @Test
    @DisplayName("every operation is recorded, in order")
    void recordsEveryOperation() {
        calculator.add(4, 5);
        calculator.subtract(10, 3);
        calculator.divide(9, 4);

        assertEquals(List.of("4 + 5 = 9", "10 - 3 = 7", "9 / 4 = 2.25"),
                log.entries());
    }

    @Test
    @DisplayName("the history cannot be edited from outside")
    void historyIsUnmodifiable() {
        calculator.add(1, 1);
        List<String> entries = calculator.history().entries();
        assertThrows(UnsupportedOperationException.class, () -> entries.add("2 + 2 = 5"));
    }

    // These two are a pair: whichever order they run in, both see an empty log,
    // which is what @BeforeEach and @AfterEach are there to guarantee.

    @Test
    @DisplayName("isolation, first of two")
    void isolationOne() {
        assertEquals(0, log.size());
        calculator.add(1, 1);
        assertEquals(1, log.size());
    }

    @Test
    @DisplayName("isolation, second of two")
    void isolationTwo() {
        assertEquals(0, log.size());
        calculator.multiply(2, 2);
        assertEquals(1, log.size());
    }

    // --------------------------------------------------------- floating point

    @Test
    @DisplayName("0.1 + 0.2 is 0.3 once the rounding policy has been applied")
    void roundingPolicyHidesRepresentationError() {
        assertEquals(0.3, calculator.add(0.1, 0.2));
    }

    @Test
    @DisplayName("without the policy the same sum is 0.30000000000000004")
    void withoutRoundingTheErrorIsVisible() {
        Calculator raw = new Calculator(new IdentityRoundingPolicy(), new NullOperationLog());

        // The exact comparison that a beginner writes, and that fails.
        assertNotEquals(0.3, raw.add(0.1, 0.2));

        // Two assertions that do hold. The three-argument assertEquals takes a
        // tolerance, and is the right assertion for a double whose last bits
        // are not meaningful.
        assertEquals(0.3, raw.add(0.1, 0.2), 1e-9);
        assertEquals(0.30000000000000004, raw.add(0.1, 0.2));
    }
}
