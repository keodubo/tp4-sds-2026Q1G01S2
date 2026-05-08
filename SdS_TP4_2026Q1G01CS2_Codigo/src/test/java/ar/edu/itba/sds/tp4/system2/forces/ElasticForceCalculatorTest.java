package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.contacts.Contact;
import ar.edu.itba.sds.tp4.system2.contacts.ContactDetector;
import ar.edu.itba.sds.tp4.system2.contacts.ContactType;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class ElasticForceCalculatorTest {
    private static final double EPS = 1e-12;
    private final System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);
    private final ContactDetector detector = new ContactDetector();
    private final ElasticForceCalculator forceCalculator = new ElasticForceCalculator(100.0);

    @Test
    void overlappingParticlesReceiveOppositeElasticForces() {
        List<DynamicParticle> particles = List.of(
                particle(0, -0.75, 10.0),
                particle(1, 0.75, 10.0)
        );

        ForceSnapshot snapshot = forceCalculator.evaluate(particles, detector.detect(particles, geometry));

        assertVectorEquals(new Vector2(-50.0, 0.0), snapshot.particleForces().get(0));
        assertVectorEquals(new Vector2(50.0, 0.0), snapshot.particleForces().get(1));
        assertVectorEquals(Vector2.ZERO, snapshot.obstacleForce());
        assertVectorEquals(Vector2.ZERO, snapshot.wallForce());
    }

    @Test
    void obstacleContactPushesParticleOutwardAndObstacleOpposite() {
        List<DynamicParticle> particles = List.of(particle(0, 1.8, 0.0));

        ForceSnapshot snapshot = forceCalculator.evaluate(particles, detector.detect(particles, geometry));

        assertVectorEquals(new Vector2(20.0, 0.0), snapshot.particleForces().get(0));
        assertVectorEquals(new Vector2(-20.0, 0.0), snapshot.obstacleForce());
        assertVectorEquals(Vector2.ZERO, snapshot.wallForce());
    }

    @Test
    void wallContactPushesParticleInwardAndWallOpposite() {
        List<DynamicParticle> particles = List.of(particle(0, 39.25, 0.0));

        ForceSnapshot snapshot = forceCalculator.evaluate(particles, detector.detect(particles, geometry));

        assertVectorEquals(new Vector2(-25.0, 0.0), snapshot.particleForces().get(0));
        assertVectorEquals(Vector2.ZERO, snapshot.obstacleForce());
        assertVectorEquals(new Vector2(25.0, 0.0), snapshot.wallForce());
    }

    @Test
    void contactForcesKeepTheRawPerContactValuesNeededForOutput() {
        List<DynamicParticle> particles = List.of(
                particle(0, -0.75, 10.0),
                particle(1, 0.75, 10.0)
        );

        ForceSnapshot snapshot = forceCalculator.evaluate(particles, detector.detect(particles, geometry));
        ContactForce contactForce = snapshot.contactForces().get(0);
        Contact contact = contactForce.contact();

        assertEquals(ContactType.PARTICLE_PARTICLE, contact.type());
        assertVectorEquals(new Vector2(-50.0, 0.0), contactForce.forceOnParticle());
        assertVectorEquals(new Vector2(50.0, 0.0), contactForce.forceOnOtherBody());
    }

    private DynamicParticle particle(int id, double x, double y) {
        return new DynamicParticle(id, new Vector2(x, y), Vector2.ZERO, 1.0, 1.0);
    }

    private void assertVectorEquals(Vector2 expected, Vector2 actual) {
        assertEquals(expected.x(), actual.x(), EPS);
        assertEquals(expected.y(), actual.y(), EPS);
    }
}
