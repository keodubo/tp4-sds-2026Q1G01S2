package ar.edu.itba.sds.tp4.system2.state;

import ar.edu.itba.sds.tp4.common.math.Vector2;

public record DynamicParticle(
        int id,
        Vector2 position,
        Vector2 velocity,
        double radius,
        double mass
) {
    public DynamicParticle {
        if (id < 0) {
            throw new IllegalArgumentException("id must be non-negative.");
        }
        if (position == null) {
            throw new IllegalArgumentException("position must not be null.");
        }
        if (velocity == null) {
            throw new IllegalArgumentException("velocity must not be null.");
        }
        if (radius <= 0.0) {
            throw new IllegalArgumentException("radius must be positive.");
        }
        if (mass <= 0.0) {
            throw new IllegalArgumentException("mass must be positive.");
        }
    }
}
