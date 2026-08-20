package com.techstart.calculator;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Returns the result untouched.
 *
 * <p>Its purpose is to make the floating point problem visible. A calculator
 * built with this policy returns 0.30000000000000004 for 0.1 + 0.2, which is
 * what the hardware actually computed, and the tests use it to show why an
 * exact assertEquals on a double is the wrong assertion to reach for.
 */
@Singleton
public class IdentityRoundingPolicy implements RoundingPolicy {

    @Inject
    public IdentityRoundingPolicy() {
    }

    @Override
    public double round(double value) {
        return value;
    }

    @Override
    public String toString() {
        return "IdentityRoundingPolicy";
    }
}
