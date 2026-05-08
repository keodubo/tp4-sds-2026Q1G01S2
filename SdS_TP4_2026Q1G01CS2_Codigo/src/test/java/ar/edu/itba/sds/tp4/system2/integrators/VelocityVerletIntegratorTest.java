package ar.edu.itba.sds.tp4.system2.integrators;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.forces.System2ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class VelocityVerletIntegratorTest {
    private static final double EPS = 1e-12;
    private final System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);
    private final ForceEvaluator evaluator = new System2ForceEvaluator(geometry, 100.0);
    private final VelocityVerletIntegrator integrator = new VelocityVerletIntegrator();

    @Test
    void particleWithoutContactsMovesWithConstantVelocity() {
        DynamicParticle particle = particle(0, 10.0, 0.0, 1.0, 2.0);
        System2State state = new System2State(7, 3.0, List.of(particle));

        IntegrationResult result = integrator.step(state, 0.25, evaluator);
        DynamicParticle next = result.nextState().particles().get(0);

        assertEquals(8, result.nextState().step());
        assertEquals(3.25, result.nextState().time(), EPS);
        assertVectorEquals(new Vector2(10.25, 0.5), next.position());
        assertVectorEquals(new Vector2(1.0, 2.0), next.velocity());
        assertTrue(result.initialForces().contacts().isEmpty());
        assertTrue(result.nextForces().contacts().isEmpty());
    }

    @Test
    void overlappingParticlesStartSeparating() {
        System2State state = new System2State(0, 0.0, List.of(
                particle(0, -0.75, 10.0, 0.0, 0.0),
                particle(1, 0.75, 10.0, 0.0, 0.0)
        ));

        IntegrationResult result = integrator.step(state, 0.1, evaluator);
        DynamicParticle left = result.nextState().particles().get(0);
        DynamicParticle right = result.nextState().particles().get(1);

        assertTrue(left.position().x() < -0.75);
        assertTrue(right.position().x() > 0.75);
        assertTrue(left.velocity().x() < 0.0);
        assertTrue(right.velocity().x() > 0.0);
    }

    @Test
    void obstacleContactAcceleratesParticleOutward() {
        System2State state = new System2State(0, 0.0, List.of(
                particle(0, 1.8, 0.0, 0.0, 0.0)
        ));

        IntegrationResult result = integrator.step(state, 0.1, evaluator);
        DynamicParticle next = result.nextState().particles().get(0);

        assertTrue(next.position().x() > 1.8);
        assertTrue(next.velocity().x() > 0.0);
    }

    @Test
    void wallContactAcceleratesParticleInward() {
        System2State state = new System2State(0, 0.0, List.of(
                particle(0, 39.25, 0.0, 0.0, 0.0)
        ));

        IntegrationResult result = integrator.step(state, 0.1, evaluator);
        DynamicParticle next = result.nextState().particles().get(0);

        assertTrue(next.position().x() < 39.25);
        assertTrue(next.velocity().x() < 0.0);
    }

    private DynamicParticle particle(int id, double x, double y, double vx, double vy) {
        return new DynamicParticle(id, new Vector2(x, y), new Vector2(vx, vy), 1.0, 1.0);
    }

    private void assertVectorEquals(Vector2 expected, Vector2 actual) {
        assertEquals(expected.x(), actual.x(), EPS);
        assertEquals(expected.y(), actual.y(), EPS);
    }
}
