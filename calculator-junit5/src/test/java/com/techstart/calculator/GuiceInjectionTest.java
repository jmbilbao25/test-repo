package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.google.inject.AbstractModule;
import com.google.inject.ConfigurationException;
import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.Scopes;
import com.google.inject.util.Modules;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/**
 * Step 4: dependency injection with Guice.
 *
 * <p>These tests are about the wiring, not the arithmetic. The question they
 * answer is whether {@link CalculatorModule} builds the object graph it claims
 * to, and whether a test can replace part of it without editing it.
 */
@Tag("injection")
@DisplayName("Dependency injection with Guice")
class GuiceInjectionTest {

    private Injector injector;

    @BeforeEach
    void createInjector() {
        // A fresh injector per test. Sharing one would share the singletons
        // inside it, and the history would leak from test to test.
        injector = Guice.createInjector(new CalculatorModule());
    }

    @Test
    @DisplayName("the module supplies a fully wired calculator")
    void moduleWiresTheCalculator() {
        Calculator calculator = injector.getInstance(Calculator.class);

        assertInstanceOf(BankersRoundingPolicy.class, calculator.roundingPolicy());
        assertInstanceOf(InMemoryOperationLog.class, calculator.history());
        assertEquals(9.0, calculator.add(4, 5));
    }

    @Test
    @DisplayName("the default scale comes through the no-argument constructor")
    void defaultScaleIsInjected() {
        BankersRoundingPolicy policy = injector.getInstance(BankersRoundingPolicy.class);
        assertEquals(BankersRoundingPolicy.DEFAULT_SCALE, policy.scale());
    }

    @Test
    @DisplayName("singleton bindings hand back the same object every time")
    void singletonsAreShared() {
        assertSame(injector.getInstance(Calculator.class),
                injector.getInstance(Calculator.class));
        assertSame(injector.getInstance(OperationLog.class),
                injector.getInstance(OperationLog.class));

        // And the log the calculator holds is that same singleton, which is the
        // part that actually matters: a second injected reference sees the
        // history the calculator is writing.
        Calculator calculator = injector.getInstance(Calculator.class);
        OperationLog log = injector.getInstance(OperationLog.class);
        calculator.add(4, 5);
        assertEquals(1, log.size());
    }

    @Test
    @DisplayName("two injectors do not share state")
    void injectorsAreIndependent() {
        Calculator first = injector.getInstance(Calculator.class);
        Calculator second = Guice.createInjector(new CalculatorModule())
                .getInstance(Calculator.class);

        assertNotSame(first, second);
        first.add(1, 1);
        assertEquals(1, first.history().size());
        assertEquals(0, second.history().size());
    }

    @Test
    @DisplayName("an unbound interface is a wiring error, reported as one")
    void unboundInterfaceIsRejected() {
        Injector empty = Guice.createInjector();
        // Guice can construct a concrete class with an @Inject constructor
        // without being told to, but it cannot invent an implementation for an
        // interface. This is the error the module exists to prevent.
        assertThrows(ConfigurationException.class,
                () -> empty.getInstance(RoundingPolicy.class));
    }

    @Nested
    @DisplayName("when a test overrides part of the module")
    class WhenOverriding {

        @Test
        @DisplayName("the log can be replaced without touching CalculatorModule")
        void logCanBeReplaced() {
            Injector overridden = Guice.createInjector(
                    Modules.override(new CalculatorModule()).with(new AbstractModule() {
                        @Override
                        protected void configure() {
                            bind(OperationLog.class).to(NullOperationLog.class)
                                    .in(Scopes.SINGLETON);
                        }
                    }));

            Calculator calculator = overridden.getInstance(Calculator.class);
            assertInstanceOf(NullOperationLog.class, calculator.history());

            calculator.add(4, 5);
            calculator.multiply(6, 7);
            assertEquals(0, calculator.history().size(), "the null log records nothing");
            // The arithmetic is untouched by the substitution.
            assertEquals(9.0, calculator.add(4, 5));
        }

        @Test
        @DisplayName("the rounding policy can be replaced, and the results change")
        void roundingCanBeReplaced() {
            Injector overridden = Guice.createInjector(
                    Modules.override(new CalculatorModule()).with(new AbstractModule() {
                        @Override
                        protected void configure() {
                            bind(RoundingPolicy.class).to(IdentityRoundingPolicy.class)
                                    .in(Scopes.SINGLETON);
                        }
                    }));

            Calculator raw = overridden.getInstance(Calculator.class);
            Calculator rounded = injector.getInstance(Calculator.class);

            assertEquals(0.30000000000000004, raw.add(0.1, 0.2));
            assertEquals(0.3, rounded.add(0.1, 0.2));
        }

        @Test
        @DisplayName("a specific instance can be bound, scale and all")
        void instanceCanBeBound() {
            BankersRoundingPolicy twoPlaces = new BankersRoundingPolicy(2);
            Injector overridden = Guice.createInjector(
                    Modules.override(new CalculatorModule()).with(new AbstractModule() {
                        @Override
                        protected void configure() {
                            bind(RoundingPolicy.class).toInstance(twoPlaces);
                        }
                    }));

            Calculator calculator = overridden.getInstance(Calculator.class);
            assertSame(twoPlaces, calculator.roundingPolicy());
            assertEquals(0.33, calculator.divide(1, 3));
            assertEquals(2.35, calculator.divide(4.7, 2));
        }
    }

    @Nested
    @DisplayName("compared with the hand-rolled injector")
    class ComparedWithSimpleInjector {

        @Test
        @DisplayName("both produce a calculator that behaves the same")
        void bothProduceTheSameBehaviour() {
            Calculator fromGuice = injector.getInstance(Calculator.class);
            Calculator fromSimple = SimpleInjector.withDefaults().get(Calculator.class);

            assertEquals(fromGuice.add(0.1, 0.2), fromSimple.add(0.1, 0.2));
            assertEquals(fromGuice.divide(9, 4), fromSimple.divide(9, 4));
            assertEquals(fromGuice.roundingPolicy().getClass(),
                    fromSimple.roundingPolicy().getClass());
            assertEquals(fromGuice.history().getClass(), fromSimple.history().getClass());
        }

        @Test
        @DisplayName("both honour @Singleton")
        void bothHonourSingleton() {
            SimpleInjector simple = SimpleInjector.withDefaults();
            assertSame(simple.get(Calculator.class), simple.get(Calculator.class));
            assertTrue(injector.getInstance(Calculator.class)
                    == injector.getInstance(Calculator.class));
        }
    }
}
