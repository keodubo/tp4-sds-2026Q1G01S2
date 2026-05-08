package ar.edu.itba.sds.tp4.system2.initialization;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public final class System2InitialStateGenerator {
    private static final double EPSILON = 1e-9;
    private static final double HIGH_DENSITY_THRESHOLD = 0.35;
    private static final double RING_SPACING_FACTOR = 2.05;

    public System2State generate(System2Config config) {
        if (config == null) {
            throw new IllegalArgumentException("config must not be null.");
        }

        Random random = new Random(config.seed());
        List<DynamicParticle> particles;
        if (estimatedAreaFraction(config) > HIGH_DENSITY_THRESHOLD) {
            particles = generateParticlesOnRings(config, random);
        } else {
            particles = tryGenerateParticlesByRandomRejection(config, random);
            if (particles == null) {
                particles = generateParticlesOnRings(config, random);
            }
        }
        return new System2State(0, 0.0, particles);
    }

    private List<DynamicParticle> tryGenerateParticlesByRandomRejection(System2Config config, Random random) {
        List<DynamicParticle> particles = new ArrayList<>(config.particleCount());
        System2Geometry geometry = config.geometry();
        double inner = geometry.innerTravelRadius();
        double outer = geometry.outerTravelRadius();
        int maxAttemptsPerParticle = Math.max(2_000, config.particleCount() * 200);

        for (int particleId = 0; particleId < config.particleCount(); particleId++) {
            boolean placed = false;
            for (int attempt = 0; attempt < maxAttemptsPerParticle; attempt++) {
                Vector2 position = randomPositionInAnnulus(inner, outer, random);
                if (doesNotOverlapAny(position, geometry.particleRadius(), particles)) {
                    particles.add(buildParticle(config, random, particleId, position));
                    placed = true;
                    break;
                }
            }
            if (!placed) {
                return null;
            }
        }
        return List.copyOf(particles);
    }

    private List<DynamicParticle> generateParticlesOnRings(System2Config config, Random random) {
        System2Geometry geometry = config.geometry();
        double spacing = RING_SPACING_FACTOR * geometry.particleRadius();
        double inner = geometry.innerTravelRadius();
        double outer = geometry.outerTravelRadius();
        double span = outer - inner;
        double edgeMargin = Math.min(geometry.particleRadius() * 0.05, span / 4.0);
        if (edgeMargin <= EPSILON) {
            throw new IllegalArgumentException("Unable to place initialization rings inside the annulus.");
        }

        List<Vector2> candidates = new ArrayList<>();
        double ringRadius = inner + edgeMargin;
        double maxRingRadius = outer - edgeMargin;
        while (ringRadius <= maxRingRadius + EPSILON) {
            double circumference = 2.0 * Math.PI * ringRadius;
            int slotCount = Math.max(1, (int) (circumference / spacing));
            double angleOffset = random.nextDouble(0.0, 2.0 * Math.PI);
            for (int slot = 0; slot < slotCount; slot++) {
                double angle = angleOffset + slot * (2.0 * Math.PI / slotCount);
                candidates.add(new Vector2(ringRadius * Math.cos(angle), ringRadius * Math.sin(angle)));
            }
            ringRadius += spacing;
        }

        Collections.shuffle(candidates, random);
        if (candidates.size() < config.particleCount()) {
            throw new IllegalArgumentException("Unable to initialize the requested number of particles inside the annulus.");
        }

        List<DynamicParticle> particles = new ArrayList<>(config.particleCount());
        for (int particleId = 0; particleId < config.particleCount(); particleId++) {
            particles.add(buildParticle(config, random, particleId, candidates.get(particleId)));
        }
        if (hasAnyOverlap(particles)) {
            throw new IllegalStateException("Ring initialization produced overlapping particles.");
        }
        return List.copyOf(particles);
    }

    private Vector2 randomPositionInAnnulus(double inner, double outer, Random random) {
        double radiusSquared = random.nextDouble(inner * inner, outer * outer);
        double radius = Math.sqrt(radiusSquared);
        double angle = random.nextDouble(0.0, 2.0 * Math.PI);
        return new Vector2(radius * Math.cos(angle), radius * Math.sin(angle));
    }

    private DynamicParticle buildParticle(System2Config config, Random random, int particleId, Vector2 position) {
        double velocityAngle = random.nextDouble(0.0, 2.0 * Math.PI);
        Vector2 velocity = new Vector2(
                config.initialSpeed() * Math.cos(velocityAngle),
                config.initialSpeed() * Math.sin(velocityAngle)
        );
        return new DynamicParticle(
                particleId,
                position,
                velocity,
                config.geometry().particleRadius(),
                config.particleMass()
        );
    }

    private boolean doesNotOverlapAny(Vector2 position, double radius, List<DynamicParticle> particles) {
        for (DynamicParticle particle : particles) {
            if (position.distanceTo(particle.position()) < radius + particle.radius() - EPSILON) {
                return false;
            }
        }
        return true;
    }

    private boolean hasAnyOverlap(List<DynamicParticle> particles) {
        for (int i = 0; i < particles.size(); i++) {
            DynamicParticle particle = particles.get(i);
            for (int j = i + 1; j < particles.size(); j++) {
                DynamicParticle other = particles.get(j);
                if (particle.position().distanceTo(other.position()) < particle.radius() + other.radius() - EPSILON) {
                    return true;
                }
            }
        }
        return false;
    }

    private double estimatedAreaFraction(System2Config config) {
        System2Geometry geometry = config.geometry();
        double annulusArea = Math.PI * (
                geometry.outerTravelRadius() * geometry.outerTravelRadius()
                        - geometry.innerTravelRadius() * geometry.innerTravelRadius()
        );
        double particleArea = Math.PI * geometry.particleRadius() * geometry.particleRadius();
        return config.particleCount() * particleArea / annulusArea;
    }
}
