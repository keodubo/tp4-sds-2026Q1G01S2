package ar.edu.itba.sds.tp4.system1;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

public record System1Parameters(
        double mass,
        double springConstant,
        double gamma,
        double finalTime,
        double initialPosition,
        double initialVelocity,
        List<Double> dts
) {
    public static final double DEFAULT_MASS = 70.0;
    public static final double DEFAULT_SPRING_CONSTANT = 10_000.0;
    public static final double DEFAULT_GAMMA = 100.0;
    public static final double DEFAULT_FINAL_TIME = 5.0;
    public static final double DEFAULT_INITIAL_POSITION = 1.0;
    public static final double DEFAULT_INITIAL_VELOCITY = -DEFAULT_GAMMA / (2.0 * DEFAULT_MASS);
    public static final List<Double> DEFAULT_DTS = List.of(0.01, 0.001, 0.0001, 0.00001);

    private static final double INTEGER_TOLERANCE = 1e-9;

    public System1Parameters {
        validatePositive("m", mass);
        validatePositive("k", springConstant);
        validateNonNegative("gamma", gamma);
        validatePositive("tf", finalTime);
        validateFinite("x0", initialPosition);
        validateFinite("v0", initialVelocity);
        dts = validateDts(dts, finalTime);
    }

    public static System1Parameters defaults() {
        return new System1Parameters(
                DEFAULT_MASS,
                DEFAULT_SPRING_CONSTANT,
                DEFAULT_GAMMA,
                DEFAULT_FINAL_TIME,
                DEFAULT_INITIAL_POSITION,
                DEFAULT_INITIAL_VELOCITY,
                DEFAULT_DTS
        );
    }

    private static List<Double> validateDts(List<Double> rawDts, double finalTime) {
        if (rawDts == null || rawDts.isEmpty()) {
            throw new IllegalArgumentException("dt list must not be empty");
        }

        Set<Double> seen = new HashSet<>();
        for (double dt : rawDts) {
            validatePositive("dt", dt);
            if (!seen.add(dt)) {
                throw new IllegalArgumentException("dt values must not contain duplicates: " + dt);
            }
            validateIntegerSteps(finalTime, dt);
        }
        return List.copyOf(rawDts);
    }

    private static void validateIntegerSteps(double finalTime, double dt) {
        double steps = finalTime / dt;
        double nearestInteger = Math.rint(steps);
        double tolerance = INTEGER_TOLERANCE * Math.max(1.0, Math.abs(steps));
        if (Math.abs(steps - nearestInteger) > tolerance) {
            throw new IllegalArgumentException("tf/dt must be an integer for dt=" + dt + " and tf=" + finalTime);
        }
    }

    private static void validatePositive(String name, double value) {
        validateFinite(name, value);
        if (value <= 0.0) {
            throw new IllegalArgumentException(name + " must be > 0");
        }
    }

    private static void validateNonNegative(String name, double value) {
        validateFinite(name, value);
        if (value < 0.0) {
            throw new IllegalArgumentException(name + " must be >= 0");
        }
    }

    private static void validateFinite(String name, double value) {
        if (!Double.isFinite(value)) {
            throw new IllegalArgumentException(name + " must be finite");
        }
    }
}
