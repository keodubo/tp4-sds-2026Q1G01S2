package ar.edu.itba.sds.tp4.system2.contacts;

import ar.edu.itba.sds.tp4.common.math.Vector2;

public record Contact(
        ContactType type,
        int particleId,
        int otherParticleId,
        double distance,
        double overlap,
        Vector2 normalFromParticleToOther
) {
    public static final int NO_PARTICLE = -1;

    public Contact {
        if (type == null) {
            throw new IllegalArgumentException("type must not be null.");
        }
        if (particleId < 0) {
            throw new IllegalArgumentException("particleId must be non-negative.");
        }
        if (type == ContactType.PARTICLE_PARTICLE && otherParticleId < 0) {
            throw new IllegalArgumentException("particle-particle contacts require otherParticleId.");
        }
        if (type != ContactType.PARTICLE_PARTICLE && otherParticleId != NO_PARTICLE) {
            throw new IllegalArgumentException("fixed-boundary contacts must use NO_PARTICLE.");
        }
        if (distance < 0.0) {
            throw new IllegalArgumentException("distance must be non-negative.");
        }
        if (overlap <= 0.0) {
            throw new IllegalArgumentException("overlap must be positive for active contacts.");
        }
        if (normalFromParticleToOther == null) {
            throw new IllegalArgumentException("normalFromParticleToOther must not be null.");
        }
    }

    public static Contact particleParticle(
            int particleId,
            int otherParticleId,
            double distance,
            double overlap,
            Vector2 normalFromParticleToOther
    ) {
        return new Contact(
                ContactType.PARTICLE_PARTICLE,
                particleId,
                otherParticleId,
                distance,
                overlap,
                normalFromParticleToOther
        );
    }

    public static Contact particleObstacle(
            int particleId,
            double distance,
            double overlap,
            Vector2 normalFromParticleToOther
    ) {
        return new Contact(
                ContactType.PARTICLE_OBSTACLE,
                particleId,
                NO_PARTICLE,
                distance,
                overlap,
                normalFromParticleToOther
        );
    }

    public static Contact particleWall(
            int particleId,
            double distance,
            double overlap,
            Vector2 normalFromParticleToOther
    ) {
        return new Contact(
                ContactType.PARTICLE_WALL,
                particleId,
                NO_PARTICLE,
                distance,
                overlap,
                normalFromParticleToOther
        );
    }
}
