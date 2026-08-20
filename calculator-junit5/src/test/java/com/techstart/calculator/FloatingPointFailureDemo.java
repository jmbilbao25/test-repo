package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertAll;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Three tests that fail on purpose, so the write-up can show what a failure
 * actually looks like.
 *
 * <p>Excluded from every normal run by the pom. To see it:
 *
 * <pre>
 *   mvn test -Pshow-failure
 * </pre>
 *
 * <p>The first is the mistake this project is designed around: comparing
 * doubles for exact equality. The second shows what {@code assertAll} adds. The
 * third shows how much better the failure reads when the assertion is given a
 * message.
 */
@DisplayName("Deliberate failures")
class FloatingPointFailureDemo {

    private Calculator raw;

    @BeforeEach
    void createRawCalculator() {
        // No rounding policy, so the representation error is not hidden.
        raw = new Calculator(new IdentityRoundingPolicy(), new InMemoryOperationLog());
    }

    @Test
    @DisplayName("exact equality on a double, which is the wrong assertion")
    void exactEqualityOnADouble() {
        // Expected 0.3, actual 0.30000000000000004. The numbers are so close
        // that the failure message is the only way to see the difference.
        assertEquals(0.3, raw.add(0.1, 0.2));
    }

    @Test
    @DisplayName("assertAll reports every failure it finds, not just the first")
    void everyFailureIsReported() {
        // Four assertions, three of which fail. The one that passes is the
        // interesting one: 0.1 * 0.3 is exactly 0.03 as a double, while
        // 0.3 - 0.2 is 0.09999999999999998 and 1.1 * 1.1 is 1.2100000000000002.
        //
        // Representation error is not a rule that applies to every decimal, it
        // depends on the particular values and the particular operation. That is
        // the reason to use a tolerance everywhere rather than only where a
        // failure has already been seen — the cases that happen to be exact
        // today give no assurance about the next ones.
        assertAll(
                () -> assertEquals(0.3, raw.add(0.1, 0.2), "add: 0.1 + 0.2"),
                () -> assertEquals(0.1, raw.subtract(0.3, 0.2), "subtract: 0.3 - 0.2"),
                () -> assertEquals(0.03, raw.multiply(0.1, 0.3), "multiply: 0.1 * 0.3"),
                () -> assertEquals(1.21, raw.multiply(1.1, 1.1), "multiply: 1.1 * 1.1"));
    }

    @Test
    @DisplayName("the same failure, with a message that explains it")
    void withAMessage() {
        double actual = raw.add(0.1, 0.2);

        // The supplier form. The string is only built when the assertion fails,
        // which matters when the message is expensive to produce.
        assertEquals(0.3, actual,
                () -> "no exact binary form for 0.1 or 0.2; compare with a tolerance");
    }
}
