package com.techstart.calculator;

import java.math.BigDecimal;
import java.math.RoundingMode;

import jakarta.inject.Inject;
import jakarta.inject.Singleton;

/**
 * Rounds to a fixed number of decimal places using HALF_EVEN.
 *
 * <p>Two separate reasons for this class:
 *
 * <p>HALF_EVEN is banker's rounding. It sends a tie to the nearest even digit
 * instead of always sending it away from zero, so a long run of rounded values
 * does not drift upwards. HALF_UP would round 2.5 and 3.5 both up; HALF_EVEN
 * gives 2 and 4.
 *
 * <p>The scale also absorbs the representation error that comes with binary
 * floating point. 0.1 + 0.2 evaluates to 0.30000000000000004, and rounding that
 * to ten places produces exactly the 0.3 a caller expects. Ten is far enough
 * out that no meaningful digit of a normal calculation is touched, and close
 * enough in to remove the noise at the end of the mantissa.
 */
@Singleton
public class BankersRoundingPolicy implements RoundingPolicy {

    public static final int DEFAULT_SCALE = 10;

    private final int scale;

    /** The binding used in production, and the one Guice calls. */
    @Inject
    public BankersRoundingPolicy() {
        this(DEFAULT_SCALE);
    }

    public BankersRoundingPolicy(int scale) {
        if (scale < 0) {
            throw new IllegalArgumentException("scale cannot be negative: " + scale);
        }
        this.scale = scale;
    }

    public int scale() {
        return scale;
    }

    @Override
    public double round(double value) {
        // BigDecimal.valueOf goes through Double.toString, which gives the
        // shortest decimal that round-trips. Using the BigDecimal(double)
        // constructor instead would preserve the full binary expansion and
        // defeat the point of rounding here.
        return BigDecimal.valueOf(value)
                .setScale(scale, RoundingMode.HALF_EVEN)
                .doubleValue();
    }

    @Override
    public String toString() {
        return "BankersRoundingPolicy(scale=" + scale + ")";
    }
}
