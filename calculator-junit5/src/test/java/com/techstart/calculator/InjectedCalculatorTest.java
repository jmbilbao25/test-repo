package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Set;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.RepeatedTest;
import org.junit.jupiter.api.RepetitionInfo;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.TestReporter;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/**
 * Step 4: dependency injection into the tests, by JUnit rather than by Guice.
 *
 * <p>There is no {@code @BeforeEach} in this class and no fixture field. Every
 * test that needs a calculator says so in its parameter list and
 * {@link CalculatorExtension} provides one; the cleanup that would have been an
 * {@code @AfterEach} lives in the extension too.
 *
 * <p>Alongside the custom resolver, JUnit has built-in ones for
 * {@link TestInfo}, {@link TestReporter} and {@link RepetitionInfo}, and they are
 * requested the same way.
 */
@Tag("injection")
@ExtendWith(CalculatorExtension.class)
@DisplayName("Dependency injection by JUnit's ParameterResolver")
class InjectedCalculatorTest {

    private final Calculator constructorInjected;

    /**
     * Constructor injection. JUnit resolves the parameter before it builds the
     * instance, which means a test class can be immutable and have no
     * uninitialised fields at all.
     */
    InjectedCalculatorTest(Calculator calculator) {
        this.constructorInjected = calculator;
    }

    @Test
    @DisplayName("the constructor was given a working calculator")
    void constructorInjectionWorks() {
        assertEquals(9.0, constructorInjected.add(4, 5));
        assertTrue(constructorInjected.roundingPolicy() instanceof BankersRoundingPolicy);
    }

    @Test
    @DisplayName("a method parameter is a different instance from the constructor's")
    void methodInjectionDiffersFromConstructorInjection(Calculator injected) {
        // Not an accident, and worth stating as a test so the behaviour is
        // recorded rather than discovered again later.
        //
        // JUnit resolves a constructor parameter against the class-level
        // ExtensionContext, before any test-scoped context exists. Because store
        // lookups fall through to ancestor stores, an extension that cached the
        // value there would hand the same calculator to every test in the class.
        // CalculatorExtension therefore only caches under a test context, and
        // gives a constructor its own instance.
        assertNotSame(constructorInjected, injected);

        // Both are fully wired, and neither has been used yet.
        assertEquals(0, constructorInjected.history().size());
        assertEquals(0, injected.history().size());
    }

    @Test
    @DisplayName("every parameter of one test method gets the same instance")
    void allParametersOfOneTestAgree(Calculator first, Calculator second, OperationLog log) {
        // One context per test execution, so one calculator for all of its
        // parameters. This is what makes it safe to ask for a collaborator and
        // the object that owns it in the same signature.
        assertSame(first, second);
        assertSame(first.history(), log);
    }

    @Test
    @DisplayName("the log can be injected on its own")
    void logInjectedDirectly(Calculator calculator, OperationLog log) {
        assertSame(calculator.history(), log);
        calculator.add(2, 3);
        assertEquals(1, log.size());
        assertEquals("2 + 3 = 5", log.entries().get(0));
    }

    @Test
    @DisplayName("TestInfo is resolved by JUnit's own built-in resolver")
    void builtInResolvers(TestInfo info, TestReporter reporter, Calculator calculator) {
        assertEquals("TestInfo is resolved by JUnit's own built-in resolver",
                info.getDisplayName());
        assertEquals(Set.of("injection"), info.getTags());
        assertTrue(info.getTestMethod().isPresent());

        // Published entries appear in the XML report, which is a better place
        // for a diagnostic than System.out.
        reporter.publishEntry("sum", String.valueOf(calculator.add(1, 2)));
    }

    @RepeatedTest(value = 3, name = "repetition {currentRepetition} of {totalRepetitions}")
    @DisplayName("each repetition is given a fresh calculator")
    void eachRepetitionIsIsolated(Calculator calculator, RepetitionInfo repetition) {
        // If the calculator leaked between repetitions this would fail on the
        // second one, because the log would already have an entry.
        assertEquals(0, calculator.history().size(),
                "repetition " + repetition.getCurrentRepetition() + " saw a used calculator");
        calculator.add(repetition.getCurrentRepetition(), 0);
        assertEquals(1, calculator.history().size());
    }

    @ParameterizedTest(name = "{0} {1} {2} = {3}")
    @DisplayName("injection and parameterization together")
    @CsvSource({"4, +, 5, 9", "10, -, 3, 7", "6, *, 7, 42", "9, /, 4, 2.25"})
    void injectionWorksWithParameterizedTests(double left, String symbol, double right,
                                              double expected, Calculator calculator) {
        // The CSV arguments are resolved positionally and must come first; the
        // injected calculator is resolved by the extension afterwards. Putting
        // the calculator first would make JUnit try to read a double into it.
        assertEquals(expected, calculator.apply(Operation.fromSymbol(symbol), left, right), 1e-9);
        assertEquals(1, calculator.history().size());
    }

    @RepeatedTest(value = 2, name = "execution {currentRepetition}")
    @DisplayName("each execution is given a different instance")
    void instancesAreNotShared(Calculator calculator, RepetitionInfo repetition) {
        // Static, so it outlives the per-test instance of this class and the two
        // executions can actually be compared.
        if (repetition.getCurrentRepetition() == 1) {
            LastSeen.instance = calculator;
            return;
        }
        assertNotSame(LastSeen.instance, calculator,
                "the calculator should not be shared between executions");
    }

    /** Somewhere outside the per-test instance to remember what was seen. */
    private static final class LastSeen {
        static Calculator instance;
    }
}
