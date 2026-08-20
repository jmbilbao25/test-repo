package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/**
 * Step 4: {@code @Nested} classes, used to group tests by the situation they are
 * about.
 *
 * <p>The gain is not cosmetic. Each inner class gets its own
 * {@code @BeforeEach}, and JUnit runs the outer one first, so a group can add to
 * the shared setup instead of repeating it. The result is that
 * {@code WhenDividing} contains only what is true about division, and the
 * failure output names the group as well as the test.
 *
 * <p>Inner classes have to be non-static for this to work, because JUnit
 * instantiates the outer class first and then the inner one against it. A static
 * nested class has no enclosing instance and its tests would not be discovered.
 */
@Tag("arithmetic")
@DisplayName("A calculator")
class CalculatorNestedTest {

    private Calculator calculator;
    private InMemoryOperationLog log;

    @BeforeEach
    void createCalculator() {
        log = new InMemoryOperationLog();
        calculator = new Calculator(new BankersRoundingPolicy(), log);
    }

    @Test
    @DisplayName("starts with an empty history")
    void startsEmpty() {
        assertEquals(0, log.size());
    }

    @Nested
    @DisplayName("when adding")
    class WhenAdding {

        @Test
        @DisplayName("uses the fixture built by the outer @BeforeEach")
        void inheritsTheFixture() {
            // Nothing was constructed in this class, and yet the calculator is
            // there: the outer @BeforeEach has already run.
            assertEquals(9.0, calculator.add(4, 5));
        }

        @Test
        @DisplayName("is commutative")
        void isCommutative() {
            assertEquals(calculator.add(2.5, 7.5), calculator.add(7.5, 2.5));
        }

        @Test
        @DisplayName("0.1 + 0.2 comes out as 0.3 because of the rounding policy")
        void floatingPointIsTidied() {
            assertEquals(0.3, calculator.add(0.1, 0.2));
        }
    }

    @Nested
    @DisplayName("when dividing")
    class WhenDividing {

        @Test
        @DisplayName("9 / 4 = 2.25")
        void divides() {
            assertEquals(2.25, calculator.divide(9, 4));
        }

        @Test
        @DisplayName("by zero, throws rather than returning Infinity")
        void byZeroThrows() {
            // What the hardware would have done, shown alongside what the
            // calculator does instead.
            assertEquals(Double.POSITIVE_INFINITY, Operation.DIVIDE.applyTo(1, 0));
            assertThrows(ArithmeticException.class, () -> calculator.divide(1, 0));
        }

        @Test
        @DisplayName("by zero, records nothing in the history")
        void byZeroIsNotLogged() {
            assertThrows(ArithmeticException.class, () -> calculator.divide(1, 0));
            assertEquals(0, log.size(), "a refused operation must not be logged");
        }

        @Test
        @DisplayName("a third cannot be represented exactly, so it is rounded")
        void oneThirdIsRounded() {
            double third = calculator.divide(1, 3);
            assertEquals(0.3333333333, third);
            assertNotEquals(1.0 / 3.0, third);
        }
    }

    @Nested
    @DisplayName("when the rounding policy is swapped out")
    class WhenRoundingIsSwapped {

        private Calculator raw;

        @BeforeEach
        void createRawCalculator() {
            // This runs after the outer @BeforeEach, so both calculators exist
            // and the two can be compared in one test.
            raw = new Calculator(new IdentityRoundingPolicy(), new NullOperationLog());
        }

        @Test
        @DisplayName("the outer @BeforeEach still ran first")
        void bothFixturesExist() {
            assertTrue(calculator.roundingPolicy() instanceof BankersRoundingPolicy);
            assertTrue(raw.roundingPolicy() instanceof IdentityRoundingPolicy);
        }

        @Test
        @DisplayName("the same sum gives two different answers")
        void sameSumDifferentAnswer() {
            assertEquals(0.3, calculator.add(0.1, 0.2));
            assertEquals(0.30000000000000004, raw.add(0.1, 0.2));
        }

        @Test
        @DisplayName("both are within a sensible tolerance of each other")
        void bothAreCloseEnough() {
            assertEquals(calculator.add(0.1, 0.2), raw.add(0.1, 0.2), 1e-9);
        }
    }

    @Nested
    @DisplayName("when the log is discarded")
    class WhenLoggingIsOff {

        private Calculator silent;

        @BeforeEach
        void createSilentCalculator() {
            silent = new Calculator(new BankersRoundingPolicy(), new NullOperationLog());
        }

        @Test
        @DisplayName("the arithmetic is unchanged")
        void arithmeticIsUnchanged() {
            assertEquals(calculator.add(4, 5), silent.add(4, 5));
        }

        @Test
        @DisplayName("nothing is recorded")
        void nothingIsRecorded() {
            silent.add(4, 5);
            silent.multiply(6, 7);
            assertEquals(0, silent.history().size());
        }

        @Test
        @DisplayName("the empty history is always the same immutable list")
        void emptyHistoryIsShared() {
            assertSame(silent.history().entries(), silent.history().entries());
        }
    }
}
