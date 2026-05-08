package ar.edu.itba.sds.tp4.system2.state;

import java.util.List;

public record System2State(long step, double time, List<DynamicParticle> particles) {
    public System2State {
        if (step < 0) {
            throw new IllegalArgumentException("step must be non-negative.");
        }
        if (time < 0.0) {
            throw new IllegalArgumentException("time must be non-negative.");
        }
        if (particles == null || particles.isEmpty()) {
            throw new IllegalArgumentException("particles must not be null or empty.");
        }
        particles = List.copyOf(particles);
    }
}
