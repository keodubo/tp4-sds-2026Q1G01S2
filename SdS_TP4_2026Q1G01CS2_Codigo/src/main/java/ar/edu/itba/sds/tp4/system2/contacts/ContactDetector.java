package ar.edu.itba.sds.tp4.system2.contacts;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;

import java.util.ArrayList;
import java.util.List;

public final class ContactDetector {
    private static final Vector2 ORIGIN = Vector2.ZERO;
    private final CellIndexParticleContactFinder particleContactFinder;

    public ContactDetector() {
        this(new CellIndexParticleContactFinder());
    }

    public ContactDetector(CellIndexParticleContactFinder particleContactFinder) {
        if (particleContactFinder == null) {
            throw new IllegalArgumentException("particleContactFinder must not be null.");
        }
        this.particleContactFinder = particleContactFinder;
    }

    public List<Contact> detect(System2State state, System2Geometry geometry) {
        return detect(state.particles(), geometry);
    }

    public List<Contact> detect(List<DynamicParticle> particles, System2Geometry geometry) {
        if (particles == null) {
            throw new IllegalArgumentException("particles must not be null.");
        }
        if (geometry == null) {
            throw new IllegalArgumentException("geometry must not be null.");
        }

        List<Contact> contacts = new ArrayList<>();
        contacts.addAll(particleContactFinder.findContacts(particles, geometry));
        detectBoundaryContacts(particles, geometry, contacts);
        return List.copyOf(contacts);
    }

    private void detectBoundaryContacts(
            List<DynamicParticle> particles,
            System2Geometry geometry,
            List<Contact> contacts
    ) {
        for (DynamicParticle particle : particles) {
            Vector2 position = particle.position();
            double radialDistance = position.norm();

            double obstacleOverlap = particle.radius() + geometry.obstacleRadius() - radialDistance;
            if (obstacleOverlap > 0.0) {
                Vector2 normalToObstacle = ORIGIN.subtract(position);
                contacts.add(Contact.particleObstacle(
                        particle.id(),
                        radialDistance,
                        obstacleOverlap,
                        normalizedContactNormal(normalToObstacle, "particle-obstacle")
                ));
            }

            double wallOverlap = radialDistance + particle.radius() - geometry.outerRadius();
            if (wallOverlap > 0.0) {
                contacts.add(Contact.particleWall(
                        particle.id(),
                        radialDistance,
                        wallOverlap,
                        normalizedContactNormal(position, "particle-wall")
                ));
            }
        }
    }

    private Vector2 normalizedContactNormal(Vector2 vector, String contactKind) {
        try {
            return vector.normalized();
        } catch (IllegalArgumentException exception) {
            throw new IllegalArgumentException("Cannot define normal for " + contactKind + " contact.", exception);
        }
    }
}
