package com.techstart.calculator;

/**
 * How a raw arithmetic result is tidied up before being returned.
 *
 * <p>This is the first of the two collaborators the calculator is given rather
 * than creates. Making rounding a policy instead of a hard-coded line is what
 * lets a test decide whether it wants to see the raw binary floating point
 * result or a rounded one.
 */
public interface RoundingPolicy {

    double round(double value);
}
