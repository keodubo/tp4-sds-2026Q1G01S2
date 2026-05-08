package ar.edu.itba.sds.tp4.system2.contacts;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ContactDetectorTest {
    private static final double EPS = 1e-12;
    private final System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);
    private final ContactDetector detector = new ContactDetector();

    @Test
    void separatedParticlesInsideAnnulusDoNotCreateContacts() {
        List<DynamicParticle> particles = List.of(
                particle(0, 10.0, 0.0),
                particle(1, 13.0, 0.0)
        );

        assertTrue(detector.detect(particles, geometry).isEmpty());
    }

    @Test
    void overlappingParticlesProduceParticleParticleContact() {
        List<DynamicParticle> particles = List.of(
                particle(0, -0.75, 10.0),
                particle(1, 0.75, 10.0)
        );

        Contact contact = onlyContactOfType(detector.detect(particles, geometry), ContactType.PARTICLE_PARTICLE);

        assertEquals(0, contact.particleId());
        assertEquals(1, contact.otherParticleId());
        assertEquals(1.5, contact.distance(), EPS);
        assertEquals(0.5, contact.overlap(), EPS);
        assertEquals(1.0, contact.normalFromParticleToOther().x(), EPS);
        assertEquals(0.0, contact.normalFromParticleToOther().y(), EPS);
    }

    @Test
    void particleInsideObstacleContactHasNormalPointingToObstacleCenter() {
        List<DynamicParticle> particles = List.of(particle(0, 1.8, 0.0));

        Contact contact = onlyContactOfType(detector.detect(particles, geometry), ContactType.PARTICLE_OBSTACLE);

        assertEquals(1.8, contact.distance(), EPS);
        assertEquals(0.2, contact.overlap(), EPS);
        assertEquals(-1.0, contact.normalFromParticleToOther().x(), EPS);
        assertEquals(0.0, contact.normalFromParticleToOther().y(), EPS);
    }

    @Test
    void particleOutsideOuterTravelRadiusContactsWall() {
        List<DynamicParticle> particles = List.of(particle(0, 39.25, 0.0));

        Contact contact = onlyContactOfType(detector.detect(particles, geometry), ContactType.PARTICLE_WALL);

        assertEquals(39.25, contact.distance(), EPS);
        assertEquals(0.25, contact.overlap(), EPS);
        assertEquals(1.0, contact.normalFromParticleToOther().x(), EPS);
        assertEquals(0.0, contact.normalFromParticleToOther().y(), EPS);
    }

    private DynamicParticle particle(int id, double x, double y) {
        return new DynamicParticle(id, new Vector2(x, y), Vector2.ZERO, 1.0, 1.0);
    }

    private Contact onlyContactOfType(List<Contact> contacts, ContactType type) {
        List<Contact> matches = contacts.stream()
                .filter(contact -> contact.type() == type)
                .toList();
        assertEquals(1, matches.size());
        return matches.get(0);
    }
}
