package com.techstart.calculator;

import org.junit.platform.suite.api.SelectClasses;
import org.junit.platform.suite.api.Suite;
import org.junit.platform.suite.api.SuiteDisplayName;

/**
 * Step 3, second half: every test class in the project, gathered into one suite.
 *
 * <p>{@code @Suite} is not part of Jupiter. It comes from
 * {@code junit-platform-suite}, and the class is run by the suite engine rather
 * than the Jupiter engine — which is why it is annotated {@code @Suite} and has
 * no {@code @Test} methods of its own. A suite is a selection, not a test.
 *
 * <p>The classes are listed explicitly with {@code @SelectClasses} rather than
 * discovered with {@code @SelectPackages}, so that adding a test class is a
 * deliberate act. A package-based suite silently grows, which is convenient
 * until something is picked up that was not meant to run — such as
 * {@link FloatingPointFailureDemo}, which fails on purpose and is not listed
 * here.
 *
 * <p>Surefire would also find every one of these classes on its own, so leaving
 * the suite in the normal run counts each test twice. The pom excludes it from
 * the default run and provides a profile for it instead:
 *
 * <pre>
 *   mvn test            # the classes, once each
 *   mvn test -Psuite    # the same tests, reached through this suite
 * </pre>
 */
@Suite
@SuiteDisplayName("Calculator: the complete test suite")
@SelectClasses({
        // Step 2: annotations and assertions
        CalculatorTest.class,
        LifecycleOrderTest.class,

        // Step 3: parameterized tests
        CalculatorParameterizedTest.class,

        // Step 4: dependency injection
        GuiceInjectionTest.class,
        SimpleInjectorTest.class,
        InjectedCalculatorTest.class,

        // Step 4: nested, dynamic and the rest
        CalculatorNestedTest.class,
        CalculatorDynamicTest.class,
        AdvancedFeaturesTest.class,
})
class CalculatorTestSuite {
}
