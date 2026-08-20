package com.techstart.calculator;

import com.google.inject.Guice;
import com.google.inject.Injector;

/**
 * Runs the calculator from the command line, so the application can be
 * demonstrated on its own rather than only through its tests.
 *
 * <pre>
 *   mvn -q compile exec:java                 # the built-in demonstration
 *   mvn -q compile exec:java -Dexec.args="7 / 2"
 * </pre>
 */
public final class CalculatorApp {

    public static void main(String[] args) {
        Injector injector = Guice.createInjector(new CalculatorModule());
        Calculator calculator = injector.getInstance(Calculator.class);

        System.out.println("Calculator, wired by Guice");
        System.out.println("  rounding : " + calculator.roundingPolicy());
        System.out.println("  log      : " + calculator.history().getClass().getSimpleName());
        System.out.println();

        if (args.length == 3) {
            evaluate(calculator, args[0], args[1], args[2]);
        } else {
            if (args.length != 0) {
                System.out.println("expected three arguments, for example: 7 / 2");
                System.out.println("running the built-in demonstration instead");
                System.out.println();
            }
            demonstrate(calculator);
        }

        System.out.println();
        System.out.println("History");
        for (String entry : calculator.history().entries()) {
            System.out.println("  " + entry);
        }
    }

    private static void evaluate(Calculator calculator, String left, String symbol, String right) {
        try {
            double result = calculator.apply(Operation.fromSymbol(symbol),
                    Double.parseDouble(left), Double.parseDouble(right));
            System.out.printf("%s %s %s = %s%n", left, symbol, right, result);
        } catch (NumberFormatException e) {
            System.out.println("not a number: " + e.getMessage());
        } catch (IllegalArgumentException | ArithmeticException e) {
            System.out.println("refused: " + e.getMessage());
        }
    }

    private static void demonstrate(Calculator calculator) {
        System.out.println("The four operations");
        System.out.println("  4 + 5      = " + calculator.add(4, 5));
        System.out.println("  10 - 3     = " + calculator.subtract(10, 3));
        System.out.println("  6 * 7      = " + calculator.multiply(6, 7));
        System.out.println("  9 / 4      = " + calculator.divide(9, 4));

        System.out.println();
        System.out.println("Rounding, which is a policy rather than a hard-coded line");
        System.out.println("  0.1 + 0.2  = " + calculator.add(0.1, 0.2)
                + "   (rounded to 10 places)");
        Calculator raw = new Calculator(new IdentityRoundingPolicy(), new NullOperationLog());
        System.out.println("  0.1 + 0.2  = " + raw.add(0.1, 0.2)
                + "   (what the hardware computed)");

        System.out.println();
        System.out.println("What it refuses");
        refuse(() -> calculator.divide(1, 0), "1 / 0");
        refuse(() -> calculator.multiply(Double.MAX_VALUE, 2), "MAX_VALUE * 2");
        refuse(() -> calculator.add(Double.NaN, 1), "NaN + 1");
        refuse(() -> Operation.fromSymbol("^"), "operation '^'");
    }

    private static void refuse(Runnable action, String label) {
        try {
            action.run();
            System.out.printf("  %-16s was allowed%n", label);
        } catch (RuntimeException e) {
            System.out.printf("  %-16s %s: %s%n", label,
                    e.getClass().getSimpleName(), e.getMessage());
        }
    }

    private CalculatorApp() {
    }
}
