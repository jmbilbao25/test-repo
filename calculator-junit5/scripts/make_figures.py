"""Builds the figures for the write-up.

Two kinds. The terminal figures are rendered from the files in results/, which
hold the real output of the commands in scripts/capture.sh. The code figures are
excerpts taken from the source files themselves, located by a marker rather than
by line number so they cannot drift out of date when the code moves.

The renderer is the one from the Day 3 assignment, imported rather than copied.

    ./scripts/capture.sh          # first, to produce results/
    python3 scripts/make_figures.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
FIG = os.path.join(ROOT, "figures")
RESULTS = os.path.join(ROOT, "results")

sys.path.insert(0, os.path.join(REPO, "todo-app", "scripts"))
try:
    import render
    from render import Renderer, numbered, terminal
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"could not import todo-app/scripts/render.py: {exc}")

MAIN = "src/main/java/com/techstart/calculator"
TEST = "src/test/java/com/techstart/calculator"

CHAR_EM = 0.602
MAX_WIDTH = 1080


# ---------------------------------------------------------------------------
# Extra colouring for the output this project produces. render.TERM_WORDS is a
# module-level list, so appending to it is enough; the patterns are chosen not to
# match anything inside the HTML the earlier rules have already inserted.
# ---------------------------------------------------------------------------
def add_term_colours() -> None:
    import re
    render.TERM_WORDS.extend([
        (re.compile(r"\u2714"), "#4ec9b0"),            # the console launcher tick
        (re.compile(r"\u21b7"), "#dcdcaa"),            # its "skipped" arrow
        (re.compile(r"BUILD SUCCESS"), "#4ec9b0"),
        (re.compile(r"BUILD FAILURE"), "#f48771"),
        (re.compile(r"<<< FAILURE!"), "#f48771"),
        (re.compile(r"\b\d+ tests successful\b"), "#4ec9b0"),
        (re.compile(r"\b\d+ tests failed\b"), "#f48771"),
        (re.compile(r"\b\d+ tests skipped\b"), "#dcdcaa"),
        (re.compile(r"\bAssertionFailedError\b|\bMultipleFailuresError\b"), "#f48771"),
    ])


# ------------------------------------------------------------------- terminal
def read(name: str) -> str:
    with open(os.path.join(RESULTS, name), encoding="utf-8") as fh:
        return fh.read().rstrip("\n")


def out(name: str) -> str:
    return os.path.join(FIG, name)


def fit(body: str, font_size: float) -> int:
    columns = max((len(line) for line in body.split("\n")), default=80)
    return max(560, min(int(columns * font_size * CHAR_EM) + 34, MAX_WIDTH))


def shell(r: Renderer, title: str, source: str, name: str,
          font_size: float = 12, keep: slice | None = None) -> None:
    """One terminal figure. keep slices the lines, for output too tall for a page."""
    body = read(source)
    if keep is not None:
        body = "\n".join(body.split("\n")[keep])
    r.shot(terminal(title, body, width=fit(body, font_size), font_size=font_size),
           out(name))


# The console launcher prints a twelve-line summary after every tree. It is worth
# showing once, not eleven times, so most of the tree figures stop at the tree.
TREE_ONLY = slice(0, -14)

SHELL_FIGURES = [
    # (figure, title, results file, font size, slice)
    ("fig-env.png", "bash - the environment", "env.txt", 12, None),
    ("fig-app.png", "bash - the calculator running", "app.txt", 11.5, None),
    ("fig-test-all.png", "bash - mvn test", "test-all.txt", 12, None),
    ("fig-per-class.png", "bash - counting each class on its own",
     "per-class.txt", 12, None),
    ("fig-lifecycle.png", "bash - callback order", "lifecycle.txt", 11.5, None),

    ("fig-tree-params.png", "bash - @CsvFileSource and @NullAndEmptySource",
     "tree-params.txt", 11.5, TREE_ONLY),
    ("fig-tree-params2.png", "bash - @EnumSource, @MethodSource, @ValueSource",
     "tree-params2.txt", 11.5, TREE_ONLY),
    ("fig-tree-nested.png", "bash - @Nested", "tree-nested.txt", 11, TREE_ONLY),
    ("fig-tree-dynamic.png", "bash - @TestFactory", "tree-dynamic.txt", 10.5, TREE_ONLY),
    ("fig-tree-injection.png", "bash - injected tests",
     "tree-injection.txt", 11, TREE_ONLY),
    ("fig-tree-advanced.png", "bash - skips, conditions and the per-class lifecycle",
     "tree-advanced.txt", 10.5, None),
    ("fig-tree-suite.png", "bash - the suite, collapsed to the class level",
     "tree-suite-summary.txt", 11.5, None),

    ("fig-test-suite.png", "bash - mvn test -Psuite", "test-suite.txt", 10, None),
    ("fig-test-tags.png", "bash - selecting by tag", "test-tags.txt", 11.5, None),
    ("fig-test-failure.png", "bash - mvn test -Pshow-failure",
     "test-failure.txt", 10, None),
]


# --------------------------------------------------------------- code figures
def excerpt(path: str, start_marker: str, end_marker: str | None = None,
            lead: int = 0, drop_tail: int = 0) -> tuple[str, int]:
    """The lines between two markers, with the real line number of the first.

    lead includes that many lines before the marker, which is how an excerpt
    starting at a @DisplayName picks up the @Test above it. drop_tail removes
    that many lines from the end, for when the natural end marker leaves a
    dangling annotation behind.
    """
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    matches = [i for i, line in enumerate(lines) if start_marker in line]
    if not matches:
        raise SystemExit(f"{path}: start marker not found: {start_marker!r}")
    first = matches[0] - lead

    last = len(lines)
    if end_marker:
        found = [i for i, line in enumerate(lines)
                 if i > matches[0] and end_marker in line]
        if not found:
            raise SystemExit(f"{path}: end marker not found: {end_marker!r}")
        last = found[0]
    if drop_tail:
        last -= drop_tail

    body = "\n".join(lines[first:last]).rstrip()
    return body, first + 1


def code_figure(r: Renderer, path: str, name: str, tabs: list[str],
                start: str, end: str | None = None, lead: int = 0,
                drop_tail: int = 0, width: int = 950,
                language: str = "java") -> None:
    snippet, line_no = excerpt(path, start, end, lead, drop_tail)
    others = "".join(f'<div class="tabx">{t}</div>' for t in tabs)
    shown = path if path == "pom.xml" else os.path.basename(path)
    body = f"""
<div class="win" style="width:{width}px">
  <div class="ebar">
    <div class="tab"><span class="ic">&#9679;</span>{os.path.basename(path)}</div>
    {others}
  </div>
  <div class="ebody">{numbered(snippet, language, start=line_no)}</div>
  <div class="sbar">
    <span>{shown}</span><span>{'XML' if language == 'xml' else 'Java'}</span>
    <span class="r"><span>Spaces: 4</span><span>UTF-8</span></span>
  </div>
</div>
"""
    r.shot(body, out(name))


MAIN_TABS = ["Operation.java", "CalculatorModule.java"]
TEST_TABS = ["CalculatorTest.java", "CalculatorTestSuite.java"]

CODE_FIGURES = [
    # ---- the application
    dict(name="fig-code-calculator.png", path=f"{MAIN}/Calculator.java",
         tabs=MAIN_TABS, start="public double apply(Operation operation",
         end="/** The operation history.", lead=6),
    dict(name="fig-code-operation.png", path=f"{MAIN}/Operation.java",
         tabs=["Calculator.java", "RoundingPolicy.java"],
         start="public enum Operation {", end="    public String symbol()"),
    dict(name="fig-code-fromsymbol.png", path=f"{MAIN}/Operation.java",
         tabs=["Calculator.java", "RoundingPolicy.java"],
         start="public static Operation fromSymbol", lead=5),
    dict(name="fig-code-rounding.png", path=f"{MAIN}/BankersRoundingPolicy.java",
         tabs=["IdentityRoundingPolicy.java", "RoundingPolicy.java"],
         start="@Singleton", end="public String toString"),
    dict(name="fig-code-log.png", path=f"{MAIN}/InMemoryOperationLog.java",
         tabs=["OperationLog.java", "NullOperationLog.java"],
         start="@Singleton", end="Drops the trailing"),

    # ---- dependency injection
    dict(name="fig-code-module.png", path=f"{MAIN}/CalculatorModule.java",
         tabs=["SimpleInjector.java", "CalculatorApp.java"],
         start="public class CalculatorModule"),
    dict(name="fig-code-injector-resolve.png", path=f"{MAIN}/SimpleInjector.java",
         tabs=["CalculatorModule.java", "Calculator.java"],
         start="private <T> T resolve(Class<T> requested",
         end="The constructor annotated"),
    dict(name="fig-code-injector-ctor.png", path=f"{MAIN}/SimpleInjector.java",
         tabs=["CalculatorModule.java", "Calculator.java"],
         start="private static Constructor<?> chooseConstructor",
         end="private static String describe", lead=8),

    # ---- step 2
    dict(name="fig-code-lifecycle.png", path=f"{TEST}/CalculatorTest.java",
         tabs=["LifecycleOrderTest.java", "CalculatorNestedTest.java"],
         start="/** Static, so it survives", end="the four ops"),
    dict(name="fig-code-assertthrows.png", path=f"{TEST}/CalculatorTest.java",
         tabs=["LifecycleOrderTest.java", "CalculatorNestedTest.java"],
         start='@DisplayName("dividing by zero throws',
         end='@DisplayName("NaN and infinite', lead=1, drop_tail=1),
    dict(name="fig-code-assertall.png", path=f"{TEST}/CalculatorTest.java",
         tabs=["LifecycleOrderTest.java", "CalculatorNestedTest.java"],
         start='@DisplayName("all four at once', end="------- refusals", lead=1),
    dict(name="fig-code-tolerance.png", path=f"{TEST}/CalculatorTest.java",
         tabs=["LifecycleOrderTest.java", "FloatingPointFailureDemo.java"],
         start='@DisplayName("without the policy the same sum', lead=1),

    # ---- step 3
    dict(name="fig-code-valuesource.png",
         path=f"{TEST}/CalculatorParameterizedTest.java",
         tabs=["CalculatorTest.java", "operations.csv"],
         start="-------------------------------------------------------------- ValueSource",
         end="---------------------------------------------------------------- CsvSource"),
    dict(name="fig-code-csvsource.png",
         path=f"{TEST}/CalculatorParameterizedTest.java",
         tabs=["CalculatorTest.java", "operations.csv"],
         start="---------------------------------------------------------------- CsvSource",
         end="------------------------------------------------------------ CsvFileSource"),
    dict(name="fig-code-csvfilesource.png",
         path=f"{TEST}/CalculatorParameterizedTest.java",
         tabs=["CalculatorTest.java", "operations.csv"],
         start="------------------------------------------------------------ CsvFileSource",
         end="--------------------------------------------------------------- MethodSource"),
    dict(name="fig-code-methodsource.png",
         path=f"{TEST}/CalculatorParameterizedTest.java",
         tabs=["CalculatorTest.java", "operations.csv"],
         start="--------------------------------------------------------------- MethodSource",
         end="----------------------------------------------------------------- EnumSource"),
    dict(name="fig-code-enumsource.png",
         path=f"{TEST}/CalculatorParameterizedTest.java",
         tabs=["CalculatorTest.java", "operations.csv"],
         start="----------------------------------------------------------------- EnumSource",
         end="--------------------------------------------------------- NullAndEmptySource"),
    dict(name="fig-code-nullempty.png",
         path=f"{TEST}/CalculatorParameterizedTest.java",
         tabs=["CalculatorTest.java", "operations.csv"],
         start="--------------------------------------------------------- NullAndEmptySource"),
    dict(name="fig-code-suite.png", path=f"{TEST}/CalculatorTestSuite.java",
         tabs=["pom.xml", "CalculatorTest.java"], start="@Suite"),

    # ---- step 4
    dict(name="fig-code-nested.png", path=f"{TEST}/CalculatorNestedTest.java",
         tabs=["CalculatorTest.java", "CalculatorDynamicTest.java"],
         start='@DisplayName("when dividing")',
         end='@DisplayName("when the rounding policy is swapped out")',
         lead=1, drop_tail=1),
    dict(name="fig-code-nested-outer.png", path=f"{TEST}/CalculatorNestedTest.java",
         tabs=["CalculatorTest.java", "CalculatorDynamicTest.java"],
         start='@DisplayName("when the rounding policy is swapped out")',
         end='@DisplayName("when the log is discarded")', lead=1, drop_tail=1),
    dict(name="fig-code-dynamic.png", path=f"{TEST}/CalculatorDynamicTest.java",
         tabs=["CalculatorNestedTest.java", "operations.csv"],
         start='@DisplayName("every operation against every operand pair")',
         end="Cases the factory works out", lead=1),
    dict(name="fig-code-dynamic-boundary.png",
         path=f"{TEST}/CalculatorDynamicTest.java",
         tabs=["CalculatorNestedTest.java", "operations.csv"],
         start='@DisplayName("squaring, up to the overflow boundary',
         end="------------------------------------------------------------------ helpers",
         lead=1),
    dict(name="fig-code-extension.png", path=f"{TEST}/CalculatorExtension.java",
         tabs=["InjectedCalculatorTest.java", "SimpleInjector.java"],
         start="public Object resolveParameter",
         end="/** Built through the hand-rolled injector", lead=1),
    dict(name="fig-code-injected.png", path=f"{TEST}/InjectedCalculatorTest.java",
         tabs=["CalculatorExtension.java", "GuiceInjectionTest.java"],
         start="private final Calculator constructorInjected;",
         end='@DisplayName("every parameter of one test method',
         drop_tail=1),
    dict(name="fig-code-guice-override.png", path=f"{TEST}/GuiceInjectionTest.java",
         tabs=["CalculatorModule.java", "SimpleInjectorTest.java"],
         start='@DisplayName("the log can be replaced without touching',
         end='@DisplayName("the rounding policy can be replaced', lead=1,
         drop_tail=1),
    dict(name="fig-code-perclass.png", path=f"{TEST}/AdvancedFeaturesTest.java",
         tabs=["CalculatorTest.java", "LifecycleOrderTest.java"],
         start='@DisplayName("with one instance for the whole class")', lead=3),
    dict(name="fig-code-timeout.png", path=f"{TEST}/AdvancedFeaturesTest.java",
         tabs=["CalculatorTest.java", "LifecycleOrderTest.java"],
         start="-------------------------------------------------------------- timeouts",
         end="------------------------------------------------------- test instances"),
    dict(name="fig-code-failuredemo.png",
         path=f"{TEST}/FloatingPointFailureDemo.java",
         tabs=["CalculatorTest.java", "IdentityRoundingPolicy.java"],
         start='@DisplayName("assertAll reports every failure it finds',
         end='@DisplayName("the same failure, with a message', lead=1,
         drop_tail=1),

    # ---- the build
    dict(name="fig-code-surefire.png", path="pom.xml", tabs=["CalculatorTestSuite.java"],
         start="<artifactId>maven-surefire-plugin</artifactId>",
         end="org.codehaus.mojo", lead=1, drop_tail=2, language="xml"),
    dict(name="fig-code-profiles.png", path="pom.xml", tabs=["CalculatorTestSuite.java"],
         start="<profiles>", end="</project>", language="xml"),
]


def main() -> None:
    os.makedirs(FIG, exist_ok=True)
    add_term_colours()

    missing = [f for _, _, source, _, _ in SHELL_FIGURES
               if not os.path.exists(os.path.join(RESULTS, source))]
    if missing:
        raise SystemExit("missing results: " + ", ".join(missing)
                         + "\nrun ./scripts/capture.sh first")

    with Renderer() as r:
        for spec in CODE_FIGURES:
            code_figure(r, **spec)
        for name, title, source, size, keep in SHELL_FIGURES:
            shell(r, title, source, name, size, keep)

    print(f"done: {len(CODE_FIGURES) + len(SHELL_FIGURES)} figures")


if __name__ == "__main__":
    main()
