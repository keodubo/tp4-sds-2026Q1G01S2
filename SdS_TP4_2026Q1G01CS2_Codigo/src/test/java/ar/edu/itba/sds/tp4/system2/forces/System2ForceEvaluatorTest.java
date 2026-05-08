package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.contacts.ContactType;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class System2ForceEvaluatorTest {
    @Test
    void evaluatesContactsAndForcesFromOneState() {
        System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);
        ForceEvaluator evaluator = new System2ForceEvaluator(geometry, 100.0);
        System2State state = new System2State(0, 0.0, List.of(
                new DynamicParticle(0, new Vector2(1.8, 0.0), Vector2.ZERO, 1.0, 1.0)
        ));

        ForceEvaluation evaluation = evaluator.evaluate(state);

        assertEquals(1, evaluation.contacts().size());
        assertEquals(ContactType.PARTICLE_OBSTACLE, evaluation.contacts().get(0).type());
        assertEquals(20.0, evaluation.snapshot().particleForces().get(0).x(), 1e-12);
        assertEquals(0.0, evaluation.snapshot().particleForces().get(0).y(), 1e-12);
    }
}
