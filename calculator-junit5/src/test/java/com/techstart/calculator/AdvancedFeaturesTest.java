package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTimeout;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assumptions.assumeTrue;
import static org.junit.jupiter.api.Assumptions.assumingThat;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.condition.DisabledOnOs;
import org.junit.jupiter.api.condition.EnabledForJreRange;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.junit.jupiter.api.condition.JRE;
import org.junit.jupiter.api.condition.OS;

/**
 * The remaining JUnit 5 features the assignment asks to be explored: skipping,
 * conditions, timeouts, assumptions and the per-class lifecycle.
 *
 * <p>The distinction that matters most here is between {@code @Disabled} and an
 * assumption. {@code @Disabled} is a decision made before the run: the test is
 * reported as skipped and its body never executes. An assumption is a decision
 * made during the run, once the test can see the environment it landed in. A
 * test guarded by an assumption that holds is a test that really ran.
 *
 * <p>Neither is the same as a failure, and reaching for {@code @Disabled} to
 * quieten a failing test is how a suite stops being trusted.
 */
@Tag("advanced")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("Advanced JUnit 5 features")
class AdvancedFeaturesTest {

    private Calculator calculator;

    @BeforeEach
    void createCalculator() {
        calculator = new Calculator(new BankersRoundingPolicy(), new InMemoryOperationLog());
    }

    // ------------------------------------------------------------- skipping

    @Test
    @Order(1)
    @Disabled("Square root is not part of the assignment; kept to show a skip is reported, not hidden")
    @DisplayName("square root, once the calculator has one")
    void squareRootIsNotImplementedYet() {
        throw new AssertionError("never executed, because @Disabled is decided before the run");
    }

    @Test
    @Order(2)
    @DisplayName("a test that only makes sense with a system property set")
    @EnabledIfSystemProperty(named = "run.slow.tests", matches = "true")
    void onlyWhenAskedFor() {
        // mvn test -Drun.slow.tests=true
        // Without the property this is reported as skipped, with the condition
        // as the reason, so it is visible rather than silently absent.
        assertEquals(9.0, calculator.add(4, 5));
    }

    @Test
    @Order(3)
    @DisplayName("conditions can also key off the OS and the JRE")
    @DisabledOnOs(value = OS.WINDOWS, disabledReason = "the path assertion below is POSIX")
    @EnabledForJreRange(min = JRE.JAVA_17)
    void environmentConditions() {
        assertTrue(java.io.File.separatorChar == '/');
    }

    // ---------------------------------------------------------- assumptions

    @Test
    @Order(4)
    @DisplayName("an assumption aborts the test rather than failing it")
    void assumptionAbortsRatherThanFails() {
        assumeTrue(Double.parseDouble("0.1") == 0.1,
                "this JVM does not parse decimal literals as expected");

        // Reached on every normal JVM, so this is a real assertion and not a
        // test that quietly does nothing.
        assertEquals(0.3, calculator.add(0.1, 0.2));
    }

    @Test
    @Order(5)
    @DisplayName("assumingThat guards one part of a test without skipping the rest")
    void assumingThatGuardsPartOfATest() {
        // Always checked.
        assertEquals(9.0, calculator.add(4, 5));

        // Only checked where the property holds; the assertions after it still
        // run either way, which is the difference from assumeTrue.
        assumingThat("true".equals(System.getProperty("run.slow.tests")),
                () -> assertEquals(0.3333333333, calculator.divide(1, 3)));

        assertEquals(42.0, calculator.multiply(6, 7));
    }

    // -------------------------------------------------------------- timeouts

    @Test
    @Order(6)
    @Timeout(value = 2, unit = TimeUnit.SECONDS)
    @DisplayName("the whole test must finish inside two seconds")
    void finishesQuickly() {
        for (int i = 0; i < 50_000; i++) {
            calculator.add(i, 1);
        }
        assertEquals(50_000, calculator.history().size());
    }

    @Test
    @Order(7)
    @DisplayName("assertTimeout measures one block rather than the whole test")
    void assertTimeoutMeasuresABlock() {
        // Some setup that is deliberately not part of what is being timed.
        for (int i = 0; i < 1_000; i++) {
            calculator.add(i, 0);
        }

        // assertTimeout runs the block on the calling thread and reports how long
        // it took if it overruns. assertTimeoutPreemptively would run it on
        // another thread and interrupt it, which is what you want for something
        // that might hang — but it also means the block no longer shares the
        // caller's thread, and anything thread-bound would break.
        double result = assertTimeout(Duration.ofSeconds(2), () -> {
            double total = 0;
            for (int i = 0; i < 10_000; i++) {
                total = calculator.add(total, 1);
            }
            return total;
        });

        assertEquals(10_000.0, result);
    }

    // ------------------------------------------------------- test instances

    @Nested
    @TestInstance(TestInstance.Lifecycle.PER_CLASS)
    @TestMethodOrder(MethodOrderer.OrderAnnotation.class)
    @DisplayName("with one instance for the whole class")
    class WithPerClassLifecycle {

        /** Not static, and yet it survives between tests, because the instance does. */
        private int callsSeen;

        @Test
        @Order(1)
        @DisplayName("first test increments a field")
        void first() {
            callsSeen++;
            assertEquals(1, callsSeen);
        }

        @Test
        @Order(2)
        @DisplayName("second test sees what the first one left behind")
        void second() {
            // Under the default PER_METHOD lifecycle this would be 1, because
            // the instance would be new. It is 2 here, which is exactly the
            // shared state PER_METHOD exists to prevent, and the reason this
            // lifecycle should be reserved for expensive read-only fixtures.
            callsSeen++;
            assertEquals(2, callsSeen);
        }

        @Test
        @Order(3)
        @DisplayName("the outer @BeforeEach still runs before each of them")
        void outerSetupStillRuns() {
            // The fixture is rebuilt every time regardless of the lifecycle, so
            // the history is empty even though callsSeen is not.
            assertEquals(0, calculator.history().size());
            callsSeen++;
            assertEquals(3, callsSeen);
        }
    }
}
