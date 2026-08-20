"""The text of the write-up.

Rendered to both .docx and .pdf by build.py, using the writers from the Day 3
assignment.

Note for anyone editing this file: the PDF writer passes every paragraph through
ReportLab, which reads a small subset of HTML. Avoid the "<" character and bare
"&" in prose and in code blocks; write them out in words, or put them in a figure
instead.
"""
from __future__ import annotations

TITLE = ("Hands-on JUnit 5: Annotations, Assertions, Parameterized Tests "
         "and Advanced Concepts")
DAY = "Day 10 Practice Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 20, 2026"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    fig = lambda name, caption, width: b.append(("fig", name, caption, width))
    code = lambda lines: b.append(("code", lines))
    note = lambda t: b.append(("note", t))
    bullets = lambda items: b.append(("bullets", items))
    table = lambda rows, widths: b.append(("table", rows, widths))
    page = lambda: b.append(("break",))

    # ======================================================== introduction
    h("Introduction")
    p("The assignment asks for a calculator with the four arithmetic "
      "operations, and a JUnit 5 test suite that exercises the annotations, "
      "the assertions, parameterized tests, test suites, dependency injection "
      "and the more advanced parts of the framework.")
    p("The calculator is small on purpose. Four operations are not interesting "
      "to implement, so the effort went into giving them something worth "
      "testing: a division that refuses rather than returning infinity, a "
      "rounding policy that can be swapped out, and an operation log that "
      "records what happened. Those three decisions are what turn the "
      "lifecycle annotations, the assertions and the injection from things "
      "demonstrated into things needed.")
    p("The result is 185 tests across nine test classes. Every figure in this "
      "document is output from a real run, produced by the two scripts in the "
      "project rather than typed by hand.")
    table([
        ["What the assignment asked for", "Where it is"],
        ["A Calculator class with the four operations",
         "Calculator.java, Operation.java"],
        ["@Test with @BeforeEach and @AfterEach",
         "CalculatorTest, LifecycleOrderTest"],
        ["assertEquals and assertThrows",
         "CalculatorTest, throughout"],
        ["@ParameterizedTest",
         "CalculatorParameterizedTest, six argument sources"],
        ["A test suite with @Suite",
         "CalculatorTestSuite"],
        ["Dependency injection, simple injector or Guice",
         "Both: SimpleInjector.java and CalculatorModule.java"],
        ["Advanced concepts: nested or dynamic tests",
         "Both: CalculatorNestedTest and CalculatorDynamicTest"],
    ], [3.05, 3.25])
    p("The environment. Guice 7 is the first release built on the "
      "jakarta.inject annotations, which is why the same annotation works for "
      "both Guice and the hand-rolled injector later on.")
    fig("fig-env.png", "Java, Maven and the three versions that matter", 4.4)

    # ======================================================== step 1
    page()
    h("Step 1: The calculator application")
    p("Four operations, and a fifth method that all four delegate to. Putting "
      "the validation in one place means it cannot be bypassed by calling a "
      "different method, and it means there is one thing to read when asking "
      "what the calculator refuses.")
    table([
        ["Method", "Result", "Refuses"],
        ["add, subtract, multiply", "the arithmetic, rounded",
         "a NaN or infinite operand; a result that overflows"],
        ["divide", "the quotient, rounded",
         "the same, and a zero divisor"],
        ["apply(Operation, a, b)", "any of the four by enum",
         "the same, and a null operation"],
        ["history()", "every operation recorded so far", "\u2014"],
    ], [1.75, 2.2, 2.35])
    p("The operations live in an enum, paired with their symbol and the raw "
      "calculation. The enum holds no validation at all, deliberately: it is "
      "the unguarded arithmetic, and having it available in that form is what "
      "lets a test show the difference between what the hardware does and what "
      "the calculator does.")
    fig("fig-code-operation.png",
        "The four operations, each with its symbol and its raw arithmetic", 6.2)
    p("A second reason for the enum is that it gives the tests a list they "
      "cannot fall behind. A parameterized test over Operation.values() covers "
      "a fifth operation the day somebody adds one, without anybody "
      "remembering to update the test.")
    p("The symbol lookup is the one piece of parsing in the project, and it is "
      "strict about what it will not accept. Null, blank and unknown symbols "
      "all produce the same refusal, which gives the parameterized tests "
      "something to check that is not arithmetic.")
    fig("fig-code-fromsymbol.png",
        "Looking an operation up by symbol, and the three ways that can fail",
        6.2)

    h("The one method that matters")
    p("Everything the calculator enforces is in apply. Three rules, and the "
      "first is the one worth explaining.")
    fig("fig-code-calculator.png",
        "All four operations funnel through this method, so the validation "
        "cannot be avoided", 6.2)
    note("Integer division by zero throws ArithmeticException, so it is easy "
         "to assume floating point division does too. It does not. IEEE-754 "
         "defines 1.0 divided by 0.0 as positive infinity and 0.0 divided by "
         "0.0 as NaN, and the JVM treats neither as an error. Without the "
         "explicit check, divide would quietly return Infinity and every test "
         "expecting an exception would fail for a reason that looks like a "
         "test bug rather than a design gap.")
    p("The overflow check is the same idea one step further out. Multiplying "
      "two large but perfectly valid numbers produces infinity, and returning "
      "that would push the problem onto the caller. The calculator treats a "
      "result it cannot represent as an error, and says which calculation "
      "caused it.")
    p("The third rule is that a NaN or infinite operand is rejected before any "
      "arithmetic happens. That one is about error messages: NaN propagates "
      "silently through every operation, so a calculation that started with "
      "one produces a NaN result and no clue where it came from.")

    h("The two collaborators, and why they exist")
    p("The calculator is given a rounding policy and an operation log through "
      "its constructor, and constructs neither. That is the whole of the "
      "dependency injection design; the containers later on are just different "
      "ways of calling this constructor.")
    p("Rounding is a policy rather than a line of code because of the oldest "
      "problem in floating point arithmetic. 0.1 and 0.2 have no exact binary "
      "representation, so their sum is 0.30000000000000004. The default policy "
      "rounds to ten decimal places, which removes the noise at the end of the "
      "mantissa without touching any digit a calculation actually cares about.")
    fig("fig-code-rounding.png",
        "Banker's rounding, and the reason the scale is ten", 6.2)
    p("HALF_EVEN is the other half of that class. It sends a tie to the "
      "nearest even digit rather than always away from zero, so a long run of "
      "rounded values does not drift upwards. There is a parameterized test "
      "further on that pins this down against the HALF_UP behaviour most "
      "people expect.")
    p("The second policy, IdentityRoundingPolicy, returns the value untouched. "
      "It exists so the tests can show the raw result, and it is the more "
      "useful of the two for explaining anything.")
    p("The log is there to give the tests an observable side effect. Without "
      "it every test could only check a return value, there would be nothing "
      "for an @AfterEach to clean up, and the lifecycle annotations would look "
      "decorative. It is bound as a singleton, which is exactly what makes the "
      "cleanup necessary.")
    fig("fig-code-log.png",
        "The log the tests assert on. Bound as a singleton, so it carries state "
        "between tests unless something clears it.", 6.2)
    p("Running the application shows all of it at once: the wiring Guice "
      "produced, the four operations, the same sum under both rounding "
      "policies, and the four things it refuses.")
    fig("fig-app.png", "The calculator run from the command line", 4.8)

    # ======================================================== step 2
    page()
    h("Step 2: Annotations and assertions")
    p("CalculatorTest is the class the assignment describes: the lifecycle "
      "annotations, assertEquals and assertThrows, applied to the four "
      "operations. Seventeen tests.")
    p("The fixture is rebuilt in @BeforeEach rather than in a field "
      "initialiser, and the log is cleared in @AfterEach. Both matter here in "
      "a way they would not if the calculator were stateless.")
    fig("fig-code-lifecycle.png",
        "The four lifecycle callbacks. @BeforeAll and @AfterAll have to be "
        "static, because they run before and after any instance exists.", 6.2)
    p("Clearing in @AfterEach rather than at the start of the next test is a "
      "small decision with a real consequence: a test that fails halfway "
      "through still leaves nothing behind for the next one.")
    p("What actually keeps the tests independent, though, is not the "
      "@BeforeEach. JUnit constructs a new instance of the test class for every "
      "@Test method. LifecycleOrderTest prints the identity hash of the "
      "instance alongside each callback, and the two hashes are different.")
    fig("fig-lifecycle.png",
        "The callback order, printed by the tests themselves. Two tests, two "
        "instances, and a fresh fixture for each.", 5.4)

    h("Assertions")
    p("The assignment names assertEquals and assertThrows. Both are used "
      "throughout, along with four others where they say something the first "
      "two cannot.")
    table([
        ["Assertion", "Used for"],
        ["assertEquals(expected, actual)",
         "an exact result, where the value is exactly representable"],
        ["assertEquals(expected, actual, delta)",
         "a double whose last bits are not meaningful"],
        ["assertThrows(type, executable)",
         "a refusal, returning the exception so the message can be checked"],
        ["assertThrowsExactly(type, executable)",
         "a refusal where a subclass would not do"],
        ["assertAll(executables...)",
         "several independent checks, all reported together"],
        ["assertNotEquals, assertSame, assertNotSame",
         "identity, and the floating point comparison that does not hold"],
    ], [2.85, 3.45])
    p("assertThrows is the one with a trap in it. The call under test has to "
      "happen inside the lambda; written outside it, the exception escapes "
      "before the assertion can catch it and the test errors instead of "
      "passing. Capturing the return value and asserting on the message is "
      "also worth the extra line, because a test that only checks the type "
      "would still pass if the calculator threw for an unrelated reason.")
    fig("fig-code-assertthrows.png",
        "Two refusals. The second one exists because 0.0 divided by 0.0 is "
        "NaN rather than infinity, and both have to be refused.", 6.2)
    p("assertAll is the assertion that changed how the arithmetic tests are "
      "written. Four separate assertEquals calls stop at the first failure, so "
      "a calculator with three broken operations takes three runs to diagnose. "
      "assertAll evaluates every executable and reports them together.")
    fig("fig-code-assertall.png",
        "One failure does not hide the other three", 6.2)

    h("The assertion that is almost always wrong")
    p("assertEquals on two doubles compares them exactly. For 9.0 that is "
      "fine. For anything that came out of a decimal fraction it is a test "
      "that will fail on a value that is correct.")
    fig("fig-code-tolerance.png",
        "The exact comparison that fails, and the two that hold", 6.2)
    p("FloatingPointFailureDemo contains three tests that fail on purpose, so "
      "the failure output can be shown rather than described. It is excluded "
      "from every normal run by the pom and has its own profile.")
    fig("fig-code-failuredemo.png",
        "Four assertions, three of which fail. The one that passes is the "
        "interesting one.", 6.2)
    fig("fig-test-failure.png",
        "The same three failures as JUnit reports them", 6.2)
    note("The multiply assertion on 0.1 and 0.3 passes, and it is absent from "
         "the list of failures for that reason: 0.1 multiplied by 0.3 is "
         "exactly 0.03 as a double, while 0.3 minus 0.2 is 0.09999999999999998 "
         "and 1.1 multiplied by 1.1 is 1.2100000000000002. Representation error "
         "is not a rule that applies to every decimal; it depends on the "
         "particular values and the particular operation. That is the argument "
         "for using a tolerance everywhere rather than only where a failure has "
         "already been seen, because the cases that happen to be exact today "
         "say nothing about the next ones.")
    p("The middle failure also shows what assertAll adds. All three failing "
      "assertions are listed under one Multiple Failures heading, from a "
      "single test, rather than the first one stopping the method.")

    # ======================================================== step 3
    page()
    h("Step 3: Parameterized tests")
    p("Sixty-six of the 185 tests come from eleven parameterized methods. Six "
      "argument sources are used, each because it is the right tool for a "
      "different job rather than to work through the API.")
    table([
        ["Source", "Used for", "Cases"],
        ["@ValueSource", "one value changing at a time", "14"],
        ["@CsvSource", "operands and an expected result, next to the test", "8"],
        ["@CsvFileSource", "the same table in a file that can grow", "10"],
        ["@MethodSource", "cases that are computed rather than typed", "16"],
        ["@EnumSource", "every operation, and it cannot fall behind", "10"],
        ["@NullAndEmptySource", "the two inputs everybody forgets", "8"],
    ], [1.85, 3.55, 0.9])
    note("@BeforeEach runs before every generated case, not once per method, so "
         "each row still gets a clean calculator. This is the difference from a "
         "@TestFactory later on, where it does not.")

    h("@ValueSource, for one changing value")
    p("The simplest source, and the right one for a property that involves a "
      "single operand: zero is the identity for addition, one is the identity "
      "for multiplication, and no numerator makes division by zero acceptable.")
    fig("fig-code-valuesource.png",
        "Three properties, fourteen cases, and no expected values to maintain",
        6.2)

    h("@CsvSource and @CsvFileSource, for a table")
    p("Once a case needs operands and an expected result, a CSV row is the "
      "clearest way to write it. The name pattern is worth setting, because "
      "the default names cases by index and a report full of case 7 is no help "
      "when one of them fails.")
    fig("fig-code-csvsource.png",
        "A table written next to the test, aligned so it reads as a table",
        6.2)
    p("The same table moved into a file, so it can grow without the test class "
      "growing. The file is the interesting part of this pairing: it is read "
      "twice in this project, once by the annotation here and once by a "
      "dynamic test later.")
    code([
        "left,symbol,right,expected",
        "4,+,5,9",
        "-2.5,+,2.5,0",
        "0.1,+,0.2,0.3",
        "10,-,3,7",
        "3,-,10,-7",
        "6,*,7,42",
        "-4,*,2.5,-10",
        "9,/,4,2.25",
        "-8,/,2,-4",
        "100,/,3,33.3333333333",
    ])
    fig("fig-code-csvfilesource.png",
        "numLinesToSkip is what skips the header row", 6.2)
    p("Both of the last two rows are there for a reason. The 0.1 plus 0.2 row "
      "passes only because the rounding policy is applied, and the 100 divided "
      "by 3 row pins down what rounding to ten places actually produces.")
    fig("fig-tree-params.png",
        "The ten rows of the file, and the eight unusable symbols, each "
        "reported as its own test", 6.0)

    h("@MethodSource, for cases that have to be computed")
    p("A factory method can produce cases that would be tedious or impossible "
      "to type. The first of these generates twelve powers of two and checks "
      "doubling against addition to itself; the second is the one that pins "
      "down banker's rounding.")
    fig("fig-code-methodsource.png",
        "Generated cases, and the four ties where HALF_EVEN and HALF_UP "
        "disagree", 6.2)
    p("The rounding cases are the useful ones. At one decimal place 0.25 "
      "rounds to 0.2 and 0.35 rounds to 0.4, because both go to the nearest "
      "even digit. HALF_UP would give 0.3 and 0.4. Four rows are enough to "
      "make the difference between the two modes a fact about the code rather "
      "than a claim in a comment.")

    h("@EnumSource, for a list that maintains itself")
    p("Three properties that should hold for every operation, whatever the "
      "operation is. Nothing here restates the list, so a fifth operation "
      "would be covered by all three the moment it is added to the enum.")
    fig("fig-code-enumsource.png",
        "Every operation, and the two that are not commutative selected by "
        "name", 6.2)
    fig("fig-tree-params2.png",
        "@EnumSource, @MethodSource and @ValueSource in the report", 5.8)

    h("@NullAndEmptySource, for the two inputs everybody forgets")
    p("A @ValueSource cannot express null. Stacking @NullAndEmptySource on top "
      "of one is what puts null and the empty string into the same test as the "
      "merely wrong symbols, which is where they belong: they are all inputs "
      "the lookup has to refuse.")
    fig("fig-code-nullempty.png",
        "Eight unusable symbols, including the two that cannot be written as a "
        "@ValueSource", 6.2)

    # ======================================================== the suite
    page()
    h("Step 3, continued: The test suite")
    p("The suite gathers all nine test classes. It is worth being precise "
      "about what it is: @Suite comes from junit-platform-suite, not from "
      "Jupiter, and the class is run by the suite engine. It has no @Test "
      "methods of its own, because a suite is a selection rather than a test.")
    fig("fig-code-suite.png",
        "Nine classes, listed explicitly and grouped by the step they belong "
        "to", 6.2)
    p("The classes are listed with @SelectClasses rather than discovered with "
      "@SelectPackages, so adding a test class to the suite is a deliberate "
      "act. A package-based suite silently grows, which is convenient until it "
      "picks up something that was not meant to run. This project has exactly "
      "such a class: FloatingPointFailureDemo fails on purpose, and it is not "
      "in the list.")

    h("The problem the suite creates")
    p("Surefire finds every one of those nine classes on its own. Leaving the "
      "suite in the default run means each test is discovered twice, once "
      "directly and once through the suite, and the reported total doubles. "
      "The suite is excluded from the default run and given a profile of its "
      "own instead.")
    fig("fig-code-surefire.png",
        "The two exclusions, and why each is there", 6.2)
    fig("fig-code-profiles.png",
        "Two profiles: one to run the suite, one to see the deliberate "
        "failures", 6.2)
    code([
        "mvn test                 # the nine classes, once each: 185 tests",
        "mvn test -Psuite         # the same 185, reached through the suite",
        "mvn test -Pshow-failure  # only the three deliberate failures",
    ])
    p("Running through the suite reports the same 185 tests, which is the "
      "point: the suite changes how the tests are reached, not what runs.")
    fig("fig-test-suite.png",
        "The suite run. The same total as the default run.", 5.8)
    p("The console launcher shows the shape of it more clearly than Surefire "
      "does. The suite engine sits above the Jupiter engine, which then reports "
      "the nine classes underneath. The full tree is 245 lines; this is the "
      "same run with only the class level kept.")
    fig("fig-tree-suite.png",
        "The suite engine, the Jupiter engine, and the nine classes", 4.8)

    # ======================================================== step 4 DI
    page()
    h("Step 4: Dependency injection")
    p("The assignment allows either a simple injector or a framework. This "
      "project has both, because writing the small one is what makes the "
      "framework's job concrete, and there are then two things to compare.")
    p("There is also a third kind of injection in the project, and it is the "
      "one specific to JUnit 5: injecting into the tests themselves rather "
      "than into the application.")

    h("Guice")
    p("Three bindings. The point of them is that they are the only place the "
      "choice of implementation is written down.")
    fig("fig-code-module.png", "The production wiring, in three lines", 6.2)
    p("What makes that worth having is what a test can then do without editing "
      "it. Modules.override replaces one binding and leaves the rest alone, so "
      "a test can swap the log for one that discards everything, or the "
      "rounding policy for one that does nothing, and show that the arithmetic "
      "is unaffected either way.")
    fig("fig-code-guice-override.png",
        "Replacing one binding without touching the module", 6.2)
    p("A fresh injector is built in @BeforeEach rather than shared across the "
      "class. Sharing one would share the singletons inside it, and the "
      "operation log would leak from test to test. The tests check that too: "
      "two injectors produce calculators whose histories are independent.")

    h("The hand-rolled injector")
    p("Eighty lines, and the idea turns out to be small. Keep a map from "
      "interface to implementation, find the constructor to call, resolve each "
      "of its parameters the same way, and cache the result if the type is a "
      "singleton.")
    fig("fig-code-injector-resolve.png",
        "The whole of resolution, including the cycle check", 6.2)
    p("Choosing the constructor is where the design decision is. Guessing at "
      "the longest one is how a container ends up building something the "
      "author did not intend, so this injector takes the constructor annotated "
      "@Inject, or the only one there is, and otherwise refuses. A clear "
      "failure at wiring time is cheaper than a puzzling object later.")
    fig("fig-code-injector-ctor.png",
        "Strict on purpose: no @Inject and more than one constructor is an "
        "error", 6.2)
    p("Writing it meant designing its failures as well as its successes, and "
      "six of the twelve tests in SimpleInjectorTest are about those: an "
      "unbound interface, a missing binding further down the graph, a "
      "dependency cycle reported with the chain that caused it, two kinds of "
      "ambiguous constructor, and a constructor that throws, where the cause "
      "reported is what the constructor threw rather than the reflection "
      "wrapper around it.")
    p("Both containers produce a calculator that behaves identically, and the "
      "tests assert that directly. What the small one does not do is the "
      "argument for the framework.")
    table([
        ["", "SimpleInjector", "Guice"],
        ["Constructor injection", "yes", "yes"],
        ["Singleton scope", "yes", "yes"],
        ["Field and method injection", "no", "yes"],
        ["Two bindings for one type, by qualifier", "no", "yes"],
        ["Providers, for objects needing construction logic", "no", "yes"],
        ["Overriding a module for a test", "no", "yes"],
        ["Cycle handling", "reports it", "reports or breaks it"],
        ["Lines of code to maintain", "about 80", "none"],
    ], [3.0, 1.75, 1.55])

    h("Injection into the tests, by JUnit")
    p("This is the mechanism that has no equivalent in JUnit 4, and the reason "
      "a JUnit 4 test class is all fields and setUp methods. A test declares "
      "what it needs as a parameter and an extension provides it.")
    fig("fig-code-extension.png",
        "A ParameterResolver, and the store lookup that decides how long the "
        "value lives", 6.2)
    p("InjectedCalculatorTest has no @BeforeEach and no fixture field at all. "
      "Every test that needs a calculator asks for one, and the cleanup that "
      "would have been an @AfterEach lives in the extension, so the guarantee "
      "is made once by the thing that owns the object instead of being "
      "restated in every test class.")
    fig("fig-code-injected.png",
        "Constructor injection, and the behaviour that had to be pinned down",
        6.2)

    h("What went wrong here, and what it taught me")
    p("The first version of the extension cached the calculator in the store "
      "of whatever context it was given. All fourteen tests passed. The "
      "isolation was gone anyway.")
    p("Printing the context during resolution showed why. JUnit resolves a "
      "constructor parameter against the class-level context, and a test "
      "method parameter against the method context:")
    code([
        "[engine:junit-jupiter]/[class:InjectedCalculatorTest]",
        "[engine:junit-jupiter]/[class:InjectedCalculatorTest]/[method:logInjected...]",
    ])
    note("Store lookups fall through to ancestor stores. Computing the value "
         "under the class-level context therefore put one calculator in the "
         "class store, and every test in the class then found that same object "
         "by inheritance. The tests still passed, because the extension's "
         "afterEach cleared the history between them, so nothing ever observed "
         "the sharing. The @RepeatedTest was the one that eventually caught "
         "it: three repetitions were being handed the same instance.")
    p("The fix is that the value is only stored when the context belongs to a "
      "test. A constructor parameter is given its own instance instead, which "
      "is still one calculator per test method, since the class is "
      "instantiated once per test. It is simply not the same one the method "
      "parameters get, and there is now a test asserting exactly that so the "
      "behaviour is recorded rather than rediscovered.")
    p("Making the two identical would have meant caching at class level, and "
      "per-test isolation is worth more than that consistency. The lesson is "
      "the one worth taking from the whole assignment: a passing suite is not "
      "the same as a correct one, and shared state is invisible precisely when "
      "something else is tidying up after it.")
    fig("fig-tree-injection.png",
        "Fourteen tests with no fixture field between them. The published "
        "TestReporter entry appears under the test that wrote it.", 4.8)

    # ======================================================== nested
    page()
    h("Step 4, continued: Nested tests")
    p("@Nested groups tests by the situation they are about. The gain is not "
      "cosmetic: each inner class gets its own @BeforeEach, and JUnit runs the "
      "outer one first, so a group can add to the shared setup instead of "
      "repeating it.")
    fig("fig-code-nested.png",
        "Everything true about division, and nothing else, in one group", 6.2)
    p("The division group is the clearest example of what the grouping buys. "
      "Four tests, all about the same operation, one of which shows the raw "
      "infinity next to the exception the calculator throws instead. Read on "
      "its own, the group is a description of how division behaves.")
    p("A group that needs more than the shared fixture adds its own callback. "
      "This one builds a second calculator with the other rounding policy, "
      "which lets a single test compare the two.")
    fig("fig-code-nested-outer.png",
        "The inner @BeforeEach runs after the outer one, so both calculators "
        "exist", 6.2)
    note("The inner classes have to be non-static. JUnit instantiates the "
         "outer class first and then the inner one against it, so a static "
         "nested class has no enclosing instance and its tests are not "
         "discovered at all.")
    p("The payoff is in the report, where the group names combine with the "
      "test names to read as sentences.")
    fig("fig-tree-nested.png",
        "Fourteen tests in four groups, and the outer test that belongs to "
        "none of them", 4.6)

    # ======================================================== dynamic
    page()
    h("Step 4, continued: Dynamic tests")
    p("A @TestFactory returns tests instead of being one. The difference from "
      "@ParameterizedTest is when the cases are decided: a parameterized "
      "test's cases are fixed at compile time by its annotation, while a "
      "factory's are whatever the code returns while the test is running.")
    table([
        ["", "@ParameterizedTest", "@TestFactory"],
        ["Cases decided", "at compile time", "at run time"],
        ["@BeforeEach runs", "before every case", "once, around the factory"],
        ["Report shape", "a flat list of cases", "a tree, via dynamicContainer"],
        ["Right for", "a known set of inputs",
         "a set that depends on something read or computed"],
    ], [1.5, 2.4, 2.4])
    p("Forty of the 185 tests are generated by three factories. The first "
      "crosses every operation with every operand pair and asserts the "
      "invariant rather than the answer: the calculator either returns a "
      "finite result and logs it once, or refuses and logs nothing.")
    fig("fig-code-dynamic.png",
        "Four operations and six operand pairs, generating twenty-four tests "
        "from one method", 6.2)
    p("dynamicContainer is what makes the failure readable. Without it a "
      "failure is reported as case 23; with it, as DIVIDE and then the pair "
      "that broke.")
    fig("fig-tree-dynamic.png",
        "The generated tree. The names come from the values, so a failure "
        "names the case.", 5.2)
    note("Dynamic tests have no lifecycle. @BeforeEach and @AfterEach run once "
         "around the whole factory, not around each generated case, so "
         "anything a case needs has to be built inside its own executable. "
         "Every factory in this class constructs its own calculator for that "
         "reason, and it is the main cost of choosing a factory over a "
         "parameterized test.")
    p("The third factory is the one that could not be written as an "
      "annotation. It searches for the largest power of ten the calculator can "
      "still square, then generates tests below that boundary that must "
      "succeed and one past it that must be refused. The boundary is not known "
      "until it has been looked for, and it comes out at ten to the 154th.")
    fig("fig-code-dynamic-boundary.png",
        "Cases derived from a value discovered during the run", 6.2)
    p("The other factory reads the same CSV file that @CsvFileSource reads, "
      "and parses it by hand. Adding a row to the file adds a test to both, "
      "without either class changing.")

    # ======================================================== advanced
    page()
    h("Other advanced features")
    p("Four more things the framework offers, each with a decision attached.")
    table([
        ["Feature", "What it is for"],
        ["@Disabled",
         "a test that should not run, reported as skipped with a reason"],
        ["@EnabledIfSystemProperty, @DisabledOnOs, @EnabledForJreRange",
         "conditions evaluated before the run"],
        ["assumeTrue, assumingThat",
         "conditions evaluated during the run, aborting rather than failing"],
        ["@Timeout, assertTimeout",
         "a limit on the whole test, or on one block inside it"],
        ["@RepeatedTest", "the same test several times, to show isolation"],
        ["@TestInstance(PER_CLASS)", "one instance for the whole class"],
    ], [2.9, 3.4])
    p("The distinction that matters most is between @Disabled and an "
      "assumption. @Disabled is decided before the run and the body never "
      "executes. An assumption is decided during the run, once the test can "
      "see the environment it landed in, and a test guarded by an assumption "
      "that holds is a test that really ran. Neither is the same as a failure, "
      "and reaching for @Disabled to quieten a failing test is how a suite "
      "stops being trusted.")
    fig("fig-code-timeout.png",
        "@Timeout bounds the whole test; assertTimeout bounds one block, so "
        "setup is not counted", 6.2)
    p("The per-class lifecycle is the one to be careful with. It creates a "
      "single instance for the whole class, which means a field survives from "
      "one test to the next. The nested group below demonstrates that by "
      "counting up across three tests, which is precisely the shared state the "
      "default lifecycle exists to prevent.")
    fig("fig-code-perclass.png",
        "Shared state, on purpose. Under the default lifecycle each of these "
        "would see 1.", 6.2)
    p("Worth noting in that group: the outer @BeforeEach still runs before "
      "every test regardless of the lifecycle, so the calculator is rebuilt "
      "each time even though the counter is not. The lifecycle changes how "
      "often the class is instantiated, not how often the callbacks fire.")
    fig("fig-tree-advanced.png",
        "Two skips, each with its reason, and the three tests sharing an "
        "instance", 6.0)

    # ======================================================== results
    page()
    h("Results")
    p("185 tests, no failures, two skipped. The two skips are the @Disabled "
      "test and the one behind a system property, and both are reported with "
      "the reason they did not run.")
    fig("fig-test-all.png", "The full run", 4.0)
    p("Surefire reports each @Nested class as its own test set, and does not "
      "reliably attribute an enclosing class's own tests to the enclosing "
      "line, so its per-class breakdown shows zero for classes that do have "
      "tests. The totals are right and the breakdown is not, so the table "
      "below counts each class on its own through the console launcher "
      "instead.")
    fig("fig-per-class.png", "Where the 185 tests come from", 4.6)
    p("The classes are tagged, which makes it possible to run part of the "
      "suite without naming classes. The three counts are consistent: 137 "
      "arithmetic plus 36 injection plus 10 advanced is 183, and the remaining "
      "two are LifecycleOrderTest, which carries no tag.")
    fig("fig-test-tags.png", "Selecting by tag", 3.6)

    h("Design decisions, collected")
    bullets([
        "Four operations funnel into one method, so the validation cannot be "
        "bypassed by choosing a different entry point.",
        "Division by zero is checked explicitly, because IEEE-754 makes it "
        "infinity rather than an error and the JVM will not object.",
        "A result that overflows is an error rather than an Infinity handed "
        "back to the caller, and a NaN operand is rejected before any "
        "arithmetic so the message says where the problem entered.",
        "Rounding is an injected policy, which is what lets the tests show "
        "both the tidy result and the raw one.",
        "The operation log is injected and stateful, which is what makes "
        "@AfterEach necessary rather than decorative.",
        "The enum is the single source of truth for the operation set, so the "
        "parameterized and dynamic tests cannot fall behind it.",
        "The suite lists its classes explicitly, so the class that fails on "
        "purpose cannot be picked up by accident.",
        "The suite and the failing demonstration are excluded from the default "
        "run and given profiles, so the reported total is not double counted.",
        "The extension caches per test rather than per class, after the "
        "class-level version was found to share one calculator with every test "
        "in the class.",
    ])

    h("Running it")
    code([
        "cd calculator-junit5",
        "",
        "mvn test                         # 185 tests",
        "mvn test -Psuite                 # the same, through @Suite",
        "mvn test -Pshow-failure          # the deliberate failures",
        "mvn test -Dgroups=injection      # by tag",
        "mvn test -Dtest=LifecycleOrderTest",
        "mvn compile exec:java            # the application",
        "",
        "./scripts/capture.sh             # regenerate results/",
        "python3 scripts/make_figures.py  # regenerate figures/",
        "python3 build.py                 # regenerate this document",
    ])
    p("Java 21 is used rather than the newer release available, because Guice 7 "
      "generates classes at run time and is only tested against LTS releases.")

    return b
