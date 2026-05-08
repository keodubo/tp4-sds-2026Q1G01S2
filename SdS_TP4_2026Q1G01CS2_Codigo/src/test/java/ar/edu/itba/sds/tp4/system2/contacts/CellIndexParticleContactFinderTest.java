package ar.edu.itba.sds.tp4.system2.contacts;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;

class CellIndexParticleContactFinderTest {
    private static final System2Geometry GEOMETRY = new System2Geometry(80.0, 1.0, 1.0);

    @Test
    void cellIndexContactsMatchBruteForceForParticlesAcrossCells() {
        List<DynamicParticle> particles = List.of(
                particle(0, -38.6, -38.6),
                particle(1, -37.1, -38.6),
                particle(2, -2.01, 8.0),
                particle(3, -0.05, 8.0),
                particle(4, 12.0, -10.0),
                particle(5, 14.1, -10.0),
                particle(6, 34.0, 18.0),
                particle(7, 35.6, 18.0)
        );

        List<Contact> contacts = new CellIndexParticleContactFinder().findContacts(particles, GEOMETRY);

        assertEquals(bruteForceContactPairs(particles), contactPairs(contacts));
    }

    private Set<String> bruteForceContactPairs(List<DynamicParticle> particles) {
        Set<String> pairs = new HashSet<>();
        for (int i = 0; i < particles.size(); i++) {
            DynamicParticle particle = particles.get(i);
            for (int j = i + 1; j < particles.size(); j++) {
                DynamicParticle other = particles.get(j);
                double distance = particle.position().distanceTo(other.position());
                if (particle.radius() + other.radius() - distance > 0.0) {
                    pairs.add(pairKey(particle.id(), other.id()));
                }
            }
        }
        return pairs;
    }

    private Set<String> contactPairs(List<Contact> contacts) {
        Set<String> pairs = new HashSet<>();
        for (Contact contact : contacts) {
            assertEquals(ContactType.PARTICLE_PARTICLE, contact.type());
            pairs.add(pairKey(contact.particleId(), contact.otherParticleId()));
        }
        return pairs;
    }

    private String pairKey(int first, int second) {
        int min = Math.min(first, second);
        int max = Math.max(first, second);
        return min + ":" + max;
    }

    private DynamicParticle particle(int id, double x, double y) {
        return new DynamicParticle(id, new Vector2(x, y), Vector2.ZERO, 1.0, 1.0);
    }
}
