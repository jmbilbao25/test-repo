#!/usr/bin/env bash
#
# Runs everything and saves the real output into results/, which is where the
# figures in the write-up come from. Nothing in results/ is typed by hand.
#
#   ./scripts/capture.sh
#
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
RESULTS="$ROOT/results"
CONSOLE_VERSION=1.12.2
CONSOLE_JAR="$HOME/.m2/repository/org/junit/platform/junit-platform-console-standalone/$CONSOLE_VERSION/junit-platform-console-standalone-$CONSOLE_VERSION.jar"

cd "$ROOT"
mkdir -p "$RESULTS"

# Guice needs Java 21; Java 25 is the sandbox default.
if [[ -d /root/.local/share/mise/installs/java/21 ]]; then
    export JAVA_HOME=/root/.local/share/mise/installs/java/21
    export PATH="$JAVA_HOME/bin:$PATH"
fi

# Strip the timestamps and absolute paths that would otherwise change on every
# run, so a re-capture produces a clean diff.
clean() {
    sed -e "s|$ROOT|.|g" \
        -e "s|$HOME|~|g" \
        -e '/^\[INFO\] Downloading/d' \
        -e '/^\[INFO\] Downloaded/d' \
        -e '/Progress ([0-9]*)/d'
}

echo "== environment"
{
    echo '$ java -version'
    java -version 2>&1
    echo
    echo '$ mvn -v'
    mvn -v 2>&1 | head -2
    echo
    echo '$ grep -A2 junit.version pom.xml'
    grep -E '<(junit|guice|surefire)\.version>' pom.xml | sed 's/^ *//'
} | clean > "$RESULTS/env.txt"

echo "== the application"
{
    echo '$ mvn -q compile exec:java'
    mvn -q -B compile exec:java 2>&1
} | clean > "$RESULTS/app.txt"

echo "== full test run"
{
    echo '$ mvn test'
    # Keep the per-class lines out of this one (they are in test-per-class.txt)
    # but keep the totals, which is the line without a "-- in" suffix.
    mvn -B test 2>&1 \
        | sed -n '/--- surefire/,$p' \
        | grep -vE '^\[(INFO|WARNING|ERROR)\] (Running |Tests run:.*-- in )' \
        | grep -vE '^@|^ +@' \
        | grep -vE '^\[INFO\] (Using auto detected|-+$|$)|T E S T S'
} | clean > "$RESULTS/test-all.txt"

echo "== full test run, per class (Surefire's own view)"
{
    echo '$ mvn test'
    mvn -B test 2>&1 | grep -E '^\[(INFO|WARNING|ERROR)\] Tests run:'
} | clean > "$RESULTS/test-per-class.txt"

echo "== lifecycle ordering"
{
    echo '$ mvn test -Dtest=LifecycleOrderTest'
    mvn -B test -Dtest=LifecycleOrderTest 2>&1 \
        | sed -n '/Running Lifecycle/,/Tests run/p'
} | clean > "$RESULTS/lifecycle.txt"

echo "== the suite"
{
    echo '$ mvn test -Psuite'
    mvn -B test -Psuite 2>&1 \
        | grep -E '^\[INFO\] Running com|^\[INFO\] Tests run:.*-- in |^\[INFO\] Tests run: [0-9]+, Fail.*Skipped: [0-9]+$|BUILD' \
        | grep -vE 'Tests run: 0,'
} | clean > "$RESULTS/test-suite.txt"

echo "== deliberate failure"
{
    echo '$ mvn test -Pshow-failure'
    # Only the frames in this project. A full JUnit stack trace is forty lines
    # of reflection and stream internals, and none of it says anything.
    #  - drop the Suppressed: blocks, since the "Multiple Failures" summary
    #    above them already lists every failure
    #  - drop every stack frame that is not in this project
    mvn -B test -Pshow-failure 2>&1 \
        | sed -n '/T E S T S/,/Results:/p' \
        | grep -vE '^\[INFO\] (-+|$)|T E S T S|Results:' \
        | awk '/^[[:space:]]+Suppressed:/ {skip=1} /^\[/ {skip=0} !skip' \
        | grep -vE '^[[:space:]]+at (org\.junit|java\.|org\.apache|jdk\.|sun\.)' \
        | grep -vE '^[[:space:]]+\.\.\. [0-9]+ more'
} | clean > "$RESULTS/test-failure.txt"

echo "== tag filtering"
{
    echo '$ mvn test -Dgroups=injection'
    mvn -B test -Dgroups=injection 2>&1 | grep -E 'Tests run:' | tail -1
    echo
    echo '$ mvn test -Dgroups=arithmetic'
    mvn -B test -Dgroups=arithmetic 2>&1 | grep -E 'Tests run:' | tail -1
    echo
    echo '$ mvn test -DexcludedGroups=advanced,injection'
    mvn -B test -DexcludedGroups=advanced,injection 2>&1 | grep -E 'Tests run:' | tail -1
} | clean > "$RESULTS/test-tags.txt"

# ---------------------------------------------------------------------------
# The console launcher, for its tree output. Surefire reports a flat list; the
# tree is what shows the @Nested grouping and the dynamic containers.
# ---------------------------------------------------------------------------
if [[ ! -f "$CONSOLE_JAR" ]]; then
    echo "fetching the console launcher"
    mvn -q -B dependency:get \
        -Dartifact="org.junit.platform:junit-platform-console-standalone:$CONSOLE_VERSION"
fi

mvn -q -B dependency:build-classpath -Dmdep.outputFile=target/cp.txt -DincludeScope=test
CP="target/classes:target/test-classes:$(cat target/cp.txt)"

# tree <output file> <label shown in the figure> <engine id> <selectors...>
#
# The engine is pinned so the tree does not carry two empty branches for the
# engines that were on the classpath but had nothing to run. LifecycleOrderTest
# prints to stdout, which the launcher does not capture, so those lines are
# dropped here rather than interleaved with the tree.
tree() {
    local out="$1"; shift
    local label="$1"; shift
    local engine="$1"; shift
    {
        echo "\$ java -jar junit-platform-console-standalone.jar execute $label"
        java -jar "$CONSOLE_JAR" execute \
            --classpath "$CP" --details=tree --disable-banner \
            --disable-ansi-colors --include-engine "$engine" "$@" 2>&1 \
            | grep -vE '^@[A-Za-z]|^ +@[A-Za-z]'
    } | clean > "$RESULTS/$out"
}

echo "== tree: nested"
tree tree-nested.txt "-c CalculatorNestedTest" junit-jupiter \
    -c com.techstart.calculator.CalculatorNestedTest

echo "== tree: dynamic"
tree tree-dynamic.txt "-m 'CalculatorDynamicTest#everyOperationAgainstEveryPair' ..." junit-jupiter \
    -m 'com.techstart.calculator.CalculatorDynamicTest#everyOperationAgainstEveryPair' \
    -m 'com.techstart.calculator.CalculatorDynamicTest#squaringUpToTheOverflowBoundary'

# A method selector has to carry the parameter types, and a @ParameterizedTest
# method has them. Without the signature the launcher cannot find the method and
# reports a discovery failure.
echo "== tree: parameterized"
tree tree-params.txt "-m 'CalculatorParameterizedTest#unusableSymbols(java.lang.String)' ..." junit-jupiter \
    -m 'com.techstart.calculator.CalculatorParameterizedTest#arithmeticFromCsvFile(double, java.lang.String, double, double)' \
    -m 'com.techstart.calculator.CalculatorParameterizedTest#unusableSymbols(java.lang.String)'

echo "== tree: enum and method sources"
tree tree-params2.txt "-m 'CalculatorParameterizedTest#everyOperationIsLogged(...)' ..." junit-jupiter \
    -m 'com.techstart.calculator.CalculatorParameterizedTest#everyOperationIsLogged(com.techstart.calculator.Operation)' \
    -m 'com.techstart.calculator.CalculatorParameterizedTest#banksRoundingBreaksTiesTowardsEven(double, double)' \
    -m 'com.techstart.calculator.CalculatorParameterizedTest#addingZeroChangesNothing(double)'

echo "== tree: injection"
tree tree-injection.txt "-c InjectedCalculatorTest" junit-jupiter \
    -c com.techstart.calculator.InjectedCalculatorTest

echo "== tree: advanced"
tree tree-advanced.txt "-c AdvancedFeaturesTest" junit-jupiter \
    -c com.techstart.calculator.AdvancedFeaturesTest

echo "== tree: the whole suite"
tree tree-suite.txt "-c CalculatorTestSuite" junit-platform-suite \
    -c com.techstart.calculator.CalculatorTestSuite

# ---------------------------------------------------------------------------
# An accurate per-class count.
#
# Surefire reports each @Nested class as its own test set and does not always
# attribute the enclosing class's own tests to the enclosing line, so
# test-per-class.txt above shows "Tests run: 0" for classes that do have tests.
# The totals are right, the breakdown is not. Running each class through the
# launcher separately gives a breakdown that adds up.
# ---------------------------------------------------------------------------
CLASSES=(
    CalculatorTest
    LifecycleOrderTest
    CalculatorParameterizedTest
    GuiceInjectionTest
    SimpleInjectorTest
    InjectedCalculatorTest
    CalculatorNestedTest
    CalculatorDynamicTest
    AdvancedFeaturesTest
)

echo "== per class, counted one class at a time"
{
    echo '$ for c in "${CLASSES[@]}"; do console-launcher --select-class "$c" --details=summary; done'
    echo
    printf '%-32s %6s %8s %9s\n' 'test class' 'tests' 'passed' 'skipped'
    printf '%-32s %6s %8s %9s\n' '--------------------------------' '-----' '------' '-------'
    total=0; passed=0; skipped=0
    for class in "${CLASSES[@]}"; do
        summary=$(java -jar "$CONSOLE_JAR" execute \
            --classpath "$CP" --details=summary --disable-banner \
            --disable-ansi-colors --include-engine junit-jupiter \
            -c "com.techstart.calculator.$class" 2>&1)
        n=$(echo "$summary"  | awk '/tests found/      {print $2}')
        ok=$(echo "$summary" | awk '/tests successful/ {print $2}')
        sk=$(echo "$summary" | awk '/tests skipped/    {print $2}')
        printf '%-32s %6s %8s %9s\n' "$class" "$n" "$ok" "$sk"
        total=$((total + n)); passed=$((passed + ok)); skipped=$((skipped + sk))
    done
    printf '%-32s %6s %8s %9s\n' '--------------------------------' '-----' '------' '-------'
    printf '%-32s %6s %8s %9s\n' 'total' "$total" "$passed" "$skipped"
} | clean > "$RESULTS/per-class.txt"

# The full suite tree is 245 lines. This is the same run with only the class
# level kept, which is what fits on a page. Class-level entries are the ones
# indented by exactly nine spaces; anything deeper is an individual test.
echo "== tree: the suite, collapsed"
{
    head -5 "$RESULTS/tree-suite.txt"
    grep -E '^ {9}[├└]─ ' "$RESULTS/tree-suite.txt"
    echo
    sed -n '/Test run finished/,$p' "$RESULTS/tree-suite.txt"
} > "$RESULTS/tree-suite-summary.txt"

echo
echo "results:"
ls -1 "$RESULTS"
