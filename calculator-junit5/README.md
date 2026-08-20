# Day 10: Hands-on JUnit 5

The write-up is **[JUnit5-Testing-Assignment.docx](../JUnit5-Testing-Assignment.docx)**,
with a **[PDF copy](../JUnit5-Testing-Assignment.pdf)** — 43 pages, 46 figures.

A calculator with the four arithmetic operations, and 185 JUnit 5 tests across
nine classes covering the lifecycle annotations, the assertions, six
parameterized argument sources, a test suite, three kinds of dependency
injection, nested tests and dynamic tests.

## Running it

```bash
cd calculator-junit5

mvn test                         # 185 tests, 2 skipped
mvn test -Psuite                 # the same 185, reached through @Suite
mvn test -Pshow-failure          # the three deliberate failures
mvn test -Dgroups=injection      # by tag: 36 tests
mvn test -Dtest=LifecycleOrderTest
mvn compile exec:java            # the application on its own
mvn compile exec:java -Dexec.args="7 / 2"
```

Java 21 rather than a newer release: Guice 7 generates classes at run time and
is only tested against LTS versions.

## The application

| Class | What it is |
| --- | --- |
| `Calculator` | The four operations, all funnelling into one `apply` method |
| `Operation` | The operations as an enum, with symbol and raw arithmetic |
| `RoundingPolicy` | Injected. `BankersRoundingPolicy` (HALF_EVEN, 10 places) or `IdentityRoundingPolicy` |
| `OperationLog` | Injected. `InMemoryOperationLog` or `NullOperationLog` |
| `CalculatorModule` | The Guice wiring, three bindings |
| `SimpleInjector` | A hand-rolled container, about 80 lines |
| `CalculatorApp` | `main`, so the calculator can be demonstrated on its own |

Three things it refuses, and each is there for a reason:

- **Division by zero.** IEEE-754 makes `1.0 / 0.0` positive infinity and
  `0.0 / 0.0` NaN, and the JVM does not consider either an error. Without an
  explicit check `divide` would quietly return `Infinity`.
- **A result that overflows.** `multiply(Double.MAX_VALUE, 2)` is infinity, and
  handing that back would push the problem to the caller.
- **A NaN or infinite operand.** NaN propagates silently, so a calculation that
  started with one produces a NaN result and no clue where it entered.

## The tests

| Class | Tests | What it covers |
| --- | --- | --- |
| `CalculatorTest` | 17 | `@BeforeAll`/`@BeforeEach`/`@AfterEach`/`@AfterAll`, `assertEquals`, `assertThrows`, `assertAll` |
| `LifecycleOrderTest` | 2 | Prints the callback order and the test instance identity |
| `CalculatorParameterizedTest` | 66 | `@ValueSource`, `@CsvSource`, `@CsvFileSource`, `@MethodSource`, `@EnumSource`, `@NullAndEmptySource` |
| `GuiceInjectionTest` | 10 | Guice wiring, and `Modules.override` in a test |
| `SimpleInjectorTest` | 12 | The hand-rolled container, six of them its failure modes |
| `InjectedCalculatorTest` | 14 | `ParameterResolver`, plus `TestInfo`/`TestReporter`/`RepetitionInfo` |
| `CalculatorNestedTest` | 14 | `@Nested`, and nested `@BeforeEach` ordering |
| `CalculatorDynamicTest` | 40 | `@TestFactory`, `dynamicContainer`, a boundary found at run time |
| `AdvancedFeaturesTest` | 10 | `@Disabled`, conditions, assumptions, `@Timeout`, `PER_CLASS` |
| **Total** | **185** | 183 pass, 2 skipped |

`CalculatorTestSuite` gathers all nine with `@Suite` and `@SelectClasses`.
`FloatingPointFailureDemo` fails on purpose. Both are excluded from the default
Surefire run and have their own profile, because the suite selects classes
Surefire already finds and would otherwise double the reported total.

## Two things worth knowing

**Constructor parameters resolve against the class-level context.** The first
version of `CalculatorExtension` cached the calculator in the store of whatever
`ExtensionContext` it was handed. All fourteen tests passed and the isolation
was gone anyway: store lookups fall through to ancestor stores, so the value
computed under the class context was inherited by every test in the class. The
`@RepeatedTest` caught it — three repetitions were getting the same instance.
The extension now only caches under a test context, and a constructor parameter
gets its own instance.

**Representation error is not uniform.** `0.1 * 0.3` is exactly `0.03` as a
double, while `0.3 - 0.2` is `0.09999999999999998` and `1.1 * 1.1` is
`1.2100000000000002`. Whether an exact comparison passes depends on the values
and the operation, which is the argument for a tolerance everywhere rather than
only where a failure has already been seen.

## Regenerating the document

Everything in `results/` is captured output; nothing is typed by hand.

```bash
./scripts/capture.sh             # runs everything, writes results/
python3 scripts/make_figures.py  # renders figures/ from results/ and the sources
python3 build.py                 # writes the .docx and .pdf
```

`make_figures.py` locates code excerpts by marker rather than line number, so
they cannot drift out of date when the source moves; `build.py` fails if a
figure a section refers to is missing.
