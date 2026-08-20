package com.techstart.calculator;

import org.junit.jupiter.api.extension.AfterEachCallback;
import org.junit.jupiter.api.extension.ExtensionContext;
import org.junit.jupiter.api.extension.ParameterContext;
import org.junit.jupiter.api.extension.ParameterResolutionException;
import org.junit.jupiter.api.extension.ParameterResolver;

/**
 * Supplies a {@link Calculator} to any constructor or test method that asks for
 * one, and clears its history afterwards.
 *
 * <p>This is JUnit 5's own dependency injection. Where Guice injects the
 * application's objects into each other, {@code ParameterResolver} injects into
 * the tests themselves: a test declares what it needs as a parameter, and the
 * extension provides it. JUnit 4 could not do this at all, which is why a JUnit 4
 * test class is all fields and {@code setUp} methods.
 *
 * <h2>Where the instance is kept, and why it matters</h2>
 *
 * <p>The calculator is held in the {@link ExtensionContext} store rather than in
 * a field of this class, because JUnit makes no promise about how many times it
 * will instantiate an extension. The store also decides the value's lifetime,
 * and that turned out to be the one real design decision in this class.
 *
 * <p>Printing the context during resolution shows that JUnit resolves a
 * <em>constructor</em> parameter against the class-level context:
 *
 * <pre>
 *   [class:InjectedCalculatorTest]                        &lt;- constructor
 *   [class:InjectedCalculatorTest]/[method:logInjected...] &lt;- test method
 * </pre>
 *
 * <p>Store lookups fall through to ancestor stores, so computing the value under
 * the class-level context puts one calculator in the class store and every test
 * in the class then finds that same object. All the tests still pass, and the
 * isolation is gone: each repetition of a {@code @RepeatedTest} inherits the
 * previous one's history.
 *
 * <p>So the value is only stored when the context belongs to a test. A
 * constructor parameter is given its own instance instead — the test class is
 * built once per test method, so that is still one calculator per test, it is
 * simply not the same one the method parameters get. Making the two identical
 * would mean storing at class level, and per-test isolation is worth more than
 * that consistency.
 *
 * <p>{@code supportsParameter} is deliberately narrow. An extension that claims
 * every parameter type collides with the built-in resolvers for
 * {@code TestInfo} and {@code TestReporter}, and JUnit treats competing
 * resolvers as an error rather than picking one.
 */
public class CalculatorExtension implements ParameterResolver, AfterEachCallback {

    private static final ExtensionContext.Namespace NAMESPACE =
            ExtensionContext.Namespace.create(CalculatorExtension.class);

    private static final String KEY = "calculator";

    @Override
    public boolean supportsParameter(ParameterContext parameterContext,
                                     ExtensionContext extensionContext) {
        Class<?> type = parameterContext.getParameter().getType();
        return type == Calculator.class || type == OperationLog.class;
    }

    @Override
    public Object resolveParameter(ParameterContext parameterContext,
                                   ExtensionContext extensionContext) {
        Calculator calculator = calculatorFor(extensionContext);
        Class<?> type = parameterContext.getParameter().getType();

        if (type == Calculator.class) {
            return calculator;
        }
        if (type == OperationLog.class) {
            // The same log the calculator writes to, so a test can be handed
            // just the log and still be asserting on the right object.
            return calculator.history();
        }
        throw new ParameterResolutionException("cannot resolve " + type.getName());
    }

    /**
     * One calculator per test execution, or a throwaway one for a constructor.
     *
     * <p>Every parameter of a single test method resolves against the same
     * context, so a method asking for both a calculator and its log gets a
     * matching pair.
     */
    private Calculator calculatorFor(ExtensionContext context) {
        if (context.getTestMethod().isEmpty()) {
            // A class-level context, which means this is constructor injection.
            // Storing here would share the value with every test in the class.
            return newCalculator();
        }
        return context.getStore(NAMESPACE)
                .getOrComputeIfAbsent(KEY, key -> newCalculator(), Calculator.class);
    }

    /** Built through the hand-rolled injector, so the wiring is not restated here. */
    private static Calculator newCalculator() {
        return SimpleInjector.withDefaults().get(Calculator.class);
    }

    /**
     * The cleanup a test would otherwise write in its own {@code @AfterEach}.
     *
     * <p>Moving it into the extension is the real payoff: the guarantee is made
     * once, by the thing that owns the object, instead of being restated in
     * every test class that uses one.
     */
    @Override
    public void afterEach(ExtensionContext context) {
        Calculator calculator = context.getStore(NAMESPACE).get(KEY, Calculator.class);
        if (calculator != null) {
            calculator.history().clear();
        }
    }
}
