package ar.edu.itba.sds.tp4.system2.model;

public record System2Config(
        System2Geometry geometry,
        int particleCount,
        double particleMass,
        double initialSpeed,
        double stiffness,
        double dt,
        long steps,
        long seed
) {
    public System2Config {
        if (geometry == null) {
            throw new IllegalArgumentException("geometry must not be null.");
        }
        if (particleCount <= 0) {
            throw new IllegalArgumentException("particleCount must be positive.");
        }
        if (particleMass <= 0.0) {
            throw new IllegalArgumentException("particleMass must be positive.");
        }
        if (initialSpeed < 0.0) {
            throw new IllegalArgumentException("initialSpeed must be non-negative.");
        }
        if (stiffness <= 0.0) {
            throw new IllegalArgumentException("stiffness must be positive.");
        }
        if (dt <= 0.0) {
            throw new IllegalArgumentException("dt must be positive.");
        }
        if (steps <= 0) {
            throw new IllegalArgumentException("steps must be positive.");
        }
    }
}
