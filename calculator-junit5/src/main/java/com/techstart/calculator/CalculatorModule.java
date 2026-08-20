package com.techstart.calculator;

import com.google.inject.AbstractModule;
import com.google.inject.Scopes;

/**
 * The production wiring.
 *
 * <p>Three lines of binding, and the point of them is that they are the only
 * place the choice of implementation is written down. A test that wants a
 * different log does not edit this module; it overrides it with
 * {@code Modules.override(...)}, which is what {@code GuiceInjectionTest} does.
 */
public class CalculatorModule extends AbstractModule {

    @Override
    protected void configure() {
        bind(RoundingPolicy.class).to(BankersRoundingPolicy.class).in(Scopes.SINGLETON);
        bind(OperationLog.class).to(InMemoryOperationLog.class).in(Scopes.SINGLETON);
        bind(Calculator.class).in(Scopes.SINGLETON);
    }
}
