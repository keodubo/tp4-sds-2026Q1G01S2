package ar.edu.itba.sds.tp4.system2.initialization;

import ar.edu.itba.sds.tp4.system2.contacts.ContactDetector;
import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;
import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class System2InitialStateGeneratorTest {
    private static final double EPS = 1e-9;
    private final System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);
    private final System2InitialStateGenerator generator = new System2InitialStateGenerator();

    @Test
    void generatedInitialStateIsReproducibleForSameConfig() {
        System2Config config = config(100, 1234L);

        System2State first = generator.generate(config);
        System2State second = generator.generate(config);

        assertEquals(first, second);
    }

    @Test
    void generatedParticlesHaveExpectedPhysicalPropertiesAndBounds() {
        System2Config config = config(100, 1234L);

        System2State state = generator.generate(config);

        assertEquals(0, state.step());
        assertEquals(0.0, state.time(), EPS);
        assertEquals(config.particleCount(), state.particles().size());

        Set<Integer> ids = new HashSet<>();
        for (DynamicParticle particle : state.particles()) {
            assertTrue(ids.add(particle.id()));
            assertEquals(config.particleMass(), particle.mass(), EPS);
            assertEquals(config.geometry().particleRadius(), particle.radius(), EPS);
            assertEquals(config.initialSpeed(), particle.velocity().norm(), EPS);

            double radialDistance = particle.position().norm();
            assertTrue(radialDistance >= geometry.innerTravelRadius() - EPS);
            assertTrue(radialDistance <= geometry.outerTravelRadius() + EPS);
        }
    }

    @Test
    void generatedStateHasNoInitialContacts() {
        System2Config config = config(100, 4321L);

        System2State state = generator.generate(config);

        assertTrue(new ContactDetector().detect(state, geometry).isEmpty());
    }

    @Test
    void highDensityCaseUsesRingFallbackWithoutOverlaps() {
        System2Config config = config(1000, 9876L);

        System2State state = generator.generate(config);

        assertEquals(1000, state.particles().size());
        assertTrue(new ContactDetector().detect(state, geometry).isEmpty());
    }

    private System2Config config(int particleCount, long seed) {
        return new System2Config(
                geometry,
                particleCount,
                1.0,
                1.0,
                100.0,
                0.01,
                100,
                seed
        );
    }
}
