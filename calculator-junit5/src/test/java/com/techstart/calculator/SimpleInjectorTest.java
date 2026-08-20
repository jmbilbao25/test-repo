package com.techstart.calculator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/**
 * Step 4: the hand-rolled injector, tested on its own.
 *
 * <p>Writing the container meant its failure modes had to be designed as well as
 * its successes, and those are what most of this class is about. The nested
 * groups separate what it does from what it refuses to do.
 */
@Tag("injection")
@DisplayName("The hand-rolled SimpleInjector")
class SimpleInjectorTest {

    @Nested
    @DisplayName("resolving")
    class Resolving {

        @Test
        @DisplayName("builds the calculator and everything it needs")
        void buildsTheGraph() {
            Calculator calculator = SimpleInjector.withDefaults().get(Calculator.class);

            assertInstanceOf(BankersRoundingPolicy.class, calculator.roundingPolicy());
            assertInstanceOf(InMemoryOperationLog.class, calculator.history());
            assertEquals(2.25, calculator.divide(9, 4));
        }

        @Test
        @DisplayName("follows a binding from interface to implementation")
        void followsBindings() {
            SimpleInjector injector = new SimpleInjector()
                    .bind(RoundingPolicy.class, IdentityRoundingPolicy.class)
                    .bind(OperationLog.class, NullOperationLog.class);

            Calculator calculator = injector.get(Calculator.class);
            assertInstanceOf(IdentityRoundingPolicy.class, calculator.roundingPolicy());
            assertEquals(0.30000000000000004, calculator.add(0.1, 0.2));
        }

        @Test
        @DisplayName("caches a @Singleton and returns it for both interface and class")
        void cachesSingletons() {
            SimpleInjector injector = SimpleInjector.withDefaults();

            assertSame(injector.get(Calculator.class), injector.get(Calculator.class));
            assertSame(injector.get(OperationLog.class), injector.get(OperationLog.class));
            // Asking by implementation type gives the same instance as asking by
            // interface, which is what stops two "singletons" existing at once.
            assertSame(injector.get(OperationLog.class),
                    injector.get(InMemoryOperationLog.class));
        }

        @Test
        @DisplayName("a ready-made instance can be supplied")
        void acceptsAnInstance() {
            BankersRoundingPolicy fourPlaces = new BankersRoundingPolicy(4);
            SimpleInjector injector = new SimpleInjector()
                    .bindInstance(RoundingPolicy.class, fourPlaces)
                    .bind(OperationLog.class, InMemoryOperationLog.class);

            Calculator calculator = injector.get(Calculator.class);
            assertSame(fourPlaces, calculator.roundingPolicy());
            assertEquals(0.3333, calculator.divide(1, 3));
        }

        @Test
        @DisplayName("two injectors share nothing")
        void injectorsAreIndependent() {
            Calculator first = SimpleInjector.withDefaults().get(Calculator.class);
            Calculator second = SimpleInjector.withDefaults().get(Calculator.class);

            assertNotSame(first, second);
            first.add(1, 1);
            assertEquals(1, first.history().size());
            assertEquals(0, second.history().size());
        }

        @Test
        @DisplayName("a class with no dependencies needs no binding at all")
        void resolvesConcreteClassesDirectly() {
            assertInstanceOf(NullOperationLog.class,
                    new SimpleInjector().get(NullOperationLog.class));
        }
    }

    @Nested
    @DisplayName("refusing")
    class Refusing {

        @Test
        @DisplayName("an interface with no binding")
        void unboundInterface() {
            IllegalStateException thrown = assertThrows(IllegalStateException.class,
                    () -> new SimpleInjector().get(OperationLog.class));
            assertTrue(thrown.getMessage().startsWith("no binding for"),
                    () -> "unexpected message: " + thrown.getMessage());
        }

        @Test
        @DisplayName("a missing binding for something further down the graph")
        void unboundDependency() {
            // The calculator itself is concrete, but one of its constructor
            // parameters cannot be resolved. The failure has to come from the
            // recursive call, not from the top-level request.
            SimpleInjector injector = new SimpleInjector()
                    .bind(RoundingPolicy.class, BankersRoundingPolicy.class);
            assertThrows(IllegalStateException.class, () -> injector.get(Calculator.class));
        }

        @Test
        @DisplayName("a dependency cycle, naming the chain")
        void dependencyCycle() {
            IllegalStateException thrown = assertThrows(IllegalStateException.class,
                    () -> new SimpleInjector().get(Ping.class));

            assertTrue(thrown.getMessage().startsWith("dependency cycle:"),
                    () -> "unexpected message: " + thrown.getMessage());
            assertTrue(thrown.getMessage().contains("Ping")
                            && thrown.getMessage().contains("Pong"),
                    () -> "the chain should name both classes: " + thrown.getMessage());
        }

        @Test
        @DisplayName("a class with several constructors and no @Inject")
        void ambiguousConstructor() {
            IllegalStateException thrown = assertThrows(IllegalStateException.class,
                    () -> new SimpleInjector().get(Ambiguous.class));
            assertTrue(thrown.getMessage().contains("none is annotated @Inject"),
                    () -> "unexpected message: " + thrown.getMessage());
        }

        @Test
        @DisplayName("a class with two @Inject constructors")
        void twoInjectConstructors() {
            IllegalStateException thrown = assertThrows(IllegalStateException.class,
                    () -> new SimpleInjector().get(DoublyAnnotated.class));
            assertTrue(thrown.getMessage().contains("more than one @Inject constructor"),
                    () -> "unexpected message: " + thrown.getMessage());
        }

        @Test
        @DisplayName("a constructor that throws, reporting the real cause")
        void constructorThatThrows() {
            IllegalStateException thrown = assertThrows(IllegalStateException.class,
                    () -> new SimpleInjector().get(Explodes.class));

            // The reflection wrapper is unwrapped, so the cause is what the
            // constructor actually threw rather than InvocationTargetException.
            assertInstanceOf(IllegalArgumentException.class, thrown.getCause());
            assertEquals("not today", thrown.getCause().getMessage());
        }
    }

    // ---------------------------------------------------------- test-only types

    /** Half of a cycle: Ping needs Pong. */
    @Singleton
    static class Ping {
        @Inject
        Ping(Pong pong) {
        }
    }

    /** The other half: Pong needs Ping. */
    @Singleton
    static class Pong {
        @Inject
        Pong(Ping ping) {
        }
    }

    /** Two constructors, neither annotated, so there is nothing to choose by. */
    static class Ambiguous {
        Ambiguous() {
        }

        Ambiguous(NullOperationLog log) {
        }
    }

    /** Annotated twice, which is a mistake rather than a choice. */
    static class DoublyAnnotated {
        @Inject
        DoublyAnnotated() {
        }

        @Inject
        DoublyAnnotated(NullOperationLog log) {
        }
    }

    /** Fails while being constructed. */
    static class Explodes {
        @Inject
        Explodes() {
            throw new IllegalArgumentException("not today");
        }
    }
}
