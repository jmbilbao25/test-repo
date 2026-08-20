package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.TestMethodOrder;

/**
 * Prints the callback order, so the write-up can show it rather than assert it.
 *
 * <p>The identity hash of the test instance is printed with each test. It is
 * different every time, which is the thing worth seeing: JUnit constructs a new
 * instance of the test class for each {@code @Test} method, and that — not the
 * {@code @BeforeEach} — is what really keeps the tests independent.
 *
 * <p>{@code @TestMethodOrder} is only here to make the output deterministic.
 * Ordering tests is normally a smell, because a test that needs to run second
 * is a test that depends on the first.
 *
 * <pre>
 *   mvn test -Dtest=LifecycleOrderTest
 * </pre>
 */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("Lifecycle callback order")
class LifecycleOrderTest {

    private Calculator calculator;

    @BeforeAll
    static void beforeAll() {
        System.out.println("@BeforeAll     once, before any test instance exists");
    }

    @BeforeEach
    void beforeEach(TestInfo info) {
        calculator = new Calculator(new BankersRoundingPolicy(), new InMemoryOperationLog());
        System.out.printf("  @BeforeEach  fresh fixture for %s%n", info.getDisplayName());
    }

    @Test
    @Order(1)
    @DisplayName("first test")
    void first() {
        System.out.printf("    @Test      first,  instance %s, log has %d entries%n",
                id(), calculator.history().size());
        calculator.add(1, 1);
        assertEquals(1, calculator.history().size());
    }

    @Test
    @Order(2)
    @DisplayName("second test")
    void second() {
        System.out.printf("    @Test      second, instance %s, log has %d entries%n",
                id(), calculator.history().size());
        // The point of the assertion: the entry the first test added is not here.
        assertEquals(0, calculator.history().size(),
                "the second test must not see the first test's entry");
    }

    @AfterEach
    void afterEach() {
        calculator.history().clear();
        System.out.println("  @AfterEach   fixture discarded");
    }

    @AfterAll
    static void afterAll() {
        System.out.println("@AfterAll      once, after the last test");
    }

    private String id() {
        return String.format("%08x", System.identityHashCode(this));
    }
}
