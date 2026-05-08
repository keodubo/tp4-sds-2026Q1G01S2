package ar.edu.itba.sds.tp4.system2.engine;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.contacts.ContactType;
import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.forces.System2ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class System2EngineTest {
    private static final double EPS = 1e-12;
    private final System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);
    private final ForceEvaluator forceEvaluator = new System2ForceEvaluator(geometry, 100.0);
    private final System2Engine engine = new System2Engine(forceEvaluator);

    @Test
    void runEmitsInitialSnapshotAndOneSnapshotPerIntegratedStep() {
        System2State initialState = new System2State(0, 0.0, List.of(
                particle(0, 10.0, 0.0, 1.0, 0.0)
        ));
        InMemorySystem2SnapshotSink sink = new InMemorySystem2SnapshotSink();

        System2RunResult result = engine.run(initialState, 0.5, 3, sink);

        assertEquals(3, result.stepsExecuted());
        assertEquals(4, result.snapshotsWritten());
        assertEquals(4, sink.snapshots().size());
        assertEquals(3, result.finalState().step());
        assertEquals(1.5, result.finalState().time(), EPS);
        assertEquals(11.5, result.finalState().particles().get(0).position().x(), EPS);
    }

    @Test
    void zeroStepRunOnlyEmitsInitialRawSnapshot() {
        System2State initialState = new System2State(4, 2.0, List.of(
                particle(0, 10.0, 0.0, 0.0, 0.0)
        ));
        InMemorySystem2SnapshotSink sink = new InMemorySystem2SnapshotSink();

        System2RunResult result = engine.run(initialState, 0.5, 0, sink);

        assertEquals(initialState, result.finalState());
        assertEquals(0, result.stepsExecuted());
        assertEquals(1, result.snapshotsWritten());
        assertEquals(initialState, sink.snapshots().get(0).state());
        assertTrue(sink.snapshots().get(0).forces().contacts().isEmpty());
    }

    @Test
    void snapshotsExposeRawContactsAndForcesButNoAnalysisState() {
        System2State initialState = new System2State(0, 0.0, List.of(
                particle(0, 1.8, 0.0, 0.0, 0.0)
        ));
        InMemorySystem2SnapshotSink sink = new InMemorySystem2SnapshotSink();

        engine.run(initialState, 0.1, 1, sink);
        System2Snapshot initialSnapshot = sink.snapshots().get(0);

        assertEquals(1, initialSnapshot.forces().contacts().size());
        assertEquals(ContactType.PARTICLE_OBSTACLE, initialSnapshot.forces().contacts().get(0).type());
        assertEquals(20.0, initialSnapshot.forces().snapshot().particleForces().get(0).x(), EPS);
        assertEquals(-20.0, initialSnapshot.forces().snapshot().obstacleForce().x(), EPS);
    }

    private DynamicParticle particle(int id, double x, double y, double vx, double vy) {
        return new DynamicParticle(id, new Vector2(x, y), new Vector2(vx, vy), 1.0, 1.0);
    }
}
