package ar.edu.itba.sds.tp4.system2.output;

import ar.edu.itba.sds.tp4.common.math.Vector2;
import ar.edu.itba.sds.tp4.system2.engine.System2Engine;
import ar.edu.itba.sds.tp4.system2.engine.System2Snapshot;
import ar.edu.itba.sds.tp4.system2.forces.System2ForceEvaluator;
import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.state.DynamicParticle;
import ar.edu.itba.sds.tp4.system2.state.System2State;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class System2CsvSnapshotSinkTest {
    private final System2Geometry geometry = new System2Geometry(80.0, 1.0, 1.0);

    @TempDir
    Path outputDirectory;

    @Test
    void metadataJsonContainsRawOutputContractFields() {
        String json = metadata().toJson();

        assertTrue(json.contains("\"system\": \"system2\""));
        assertTrue(json.contains("\"run_id\": \"run-1\""));
        assertTrue(json.contains("\"L\": 80.0"));
        assertTrue(json.contains("\"L_meaning\": \"diameter\""));
        assertTrue(json.contains("\"R\": 40.0"));
        assertTrue(json.contains("\"k\": 100.0"));
        assertTrue(json.contains("\"integrator\": \"velocity_verlet\""));
        assertTrue(json.contains("\"normal_convention\""));
    }

    @Test
    void writesMetadataStatesContactsAndBoundaryForcesFiles() throws Exception {
        System2State initialState = new System2State(0, 0.0, List.of(
                new DynamicParticle(0, new Vector2(1.8, 0.0), Vector2.ZERO, 1.0, 1.0)
        ));
        System2Engine engine = new System2Engine(new System2ForceEvaluator(geometry, 100.0));

        try (System2CsvSnapshotSink sink = new System2CsvSnapshotSink(outputDirectory, metadata())) {
            engine.run(initialState, 0.1, 0, sink);
        }

        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.METADATA_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.STATES_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.CONTACTS_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.BOUNDARY_FORCES_FILE_NAME)));

        List<String> states = Files.readAllLines(outputDirectory.resolve(System2CsvSnapshotSink.STATES_FILE_NAME));
        assertEquals("step,t,particle_id,x,y,vx,vy", states.get(0));
        assertFalse(states.get(0).contains("used"));
        assertFalse(states.get(0).contains("fresh"));
        assertEquals("0,0.0,0,1.8,0.0,0.0,0.0", states.get(1));

        List<String> contacts = Files.readAllLines(outputDirectory.resolve(System2CsvSnapshotSink.CONTACTS_FILE_NAME));
        assertEquals("step,t,contact_type,i,j,distance,overlap,nx,ny,fx_i,fy_i,fx_j,fy_j", contacts.get(0));
        String[] contactFields = contacts.get(1).split(",");
        assertEquals("particle_obstacle", contactFields[2]);
        assertEquals("0", contactFields[3]);
        assertEquals("obstacle", contactFields[4]);
        assertEquals("1.8", contactFields[5]);
        assertEquals("-1.0", contactFields[7]);
        assertEquals(20.0, Double.parseDouble(contactFields[9]), 1e-12);
        assertEquals(-20.0, Double.parseDouble(contactFields[11]), 1e-12);

        List<String> boundaryForces = Files.readAllLines(
                outputDirectory.resolve(System2CsvSnapshotSink.BOUNDARY_FORCES_FILE_NAME)
        );
        assertEquals(
                "step,t,fx_obstacle,fy_obstacle,fx_wall,fy_wall,n_obstacle_contacts,n_wall_contacts",
                boundaryForces.get(0)
        );
        String[] boundaryFields = boundaryForces.get(1).split(",");
        assertEquals("0", boundaryFields[0]);
        assertEquals(0.0, Double.parseDouble(boundaryFields[1]), 1e-12);
        assertEquals(-20.0, Double.parseDouble(boundaryFields[2]), 1e-12);
        assertEquals(0.0, Double.parseDouble(boundaryFields[3]), 1e-12);
        assertEquals(0.0, Double.parseDouble(boundaryFields[4]), 1e-12);
        assertEquals(0.0, Double.parseDouble(boundaryFields[5]), 1e-12);
        assertEquals("1", boundaryFields[6]);
        assertEquals("0", boundaryFields[7]);
    }

    @Test
    void rejectsWritesAfterClose() {
        System2CsvSnapshotSink sink = new System2CsvSnapshotSink(outputDirectory, metadata());
        sink.close();

        System2State state = new System2State(0, 0.0, List.of(
                new DynamicParticle(0, new Vector2(10.0, 0.0), Vector2.ZERO, 1.0, 1.0)
        ));
        System2Engine engine = new System2Engine(new System2ForceEvaluator(geometry, 100.0));

        assertThrows(IllegalStateException.class, () -> engine.run(state, 0.1, 0, sink));
    }

    @Test
    void outputSamplingKeepsObstacleContactsAtEveryIntegrationStep() throws Exception {
        System2ForceEvaluator evaluator = new System2ForceEvaluator(geometry, 100.0);
        System2OutputConfig outputConfig = new System2OutputConfig(2, 3, 2);

        try (System2CsvSnapshotSink sink = new System2CsvSnapshotSink(outputDirectory, metadata(), outputConfig)) {
            for (int step = 0; step <= 3; step++) {
                System2State state = new System2State(step, step * 0.1, List.of(
                        new DynamicParticle(0, new Vector2(1.8, 0.0), Vector2.ZERO, 1.0, 1.0)
                ));
                sink.accept(new System2Snapshot(state, evaluator.evaluate(state)));
            }
        }

        List<String> states = Files.readAllLines(outputDirectory.resolve(System2CsvSnapshotSink.STATES_FILE_NAME));
        assertEquals(4, states.size());
        assertTrue(states.get(1).startsWith("0,"));
        assertTrue(states.get(2).startsWith("2,"));
        assertTrue(states.get(3).startsWith("3,"));

        List<String> contacts = Files.readAllLines(outputDirectory.resolve(System2CsvSnapshotSink.CONTACTS_FILE_NAME));
        assertEquals(5, contacts.size());
        assertTrue(contacts.get(1).startsWith("0,"));
        assertTrue(contacts.get(2).startsWith("1,"));
        assertTrue(contacts.get(3).startsWith("2,"));
        assertTrue(contacts.get(4).startsWith("3,"));

        List<String> boundaryForces = Files.readAllLines(
                outputDirectory.resolve(System2CsvSnapshotSink.BOUNDARY_FORCES_FILE_NAME)
        );
        assertEquals(3, boundaryForces.size());
        assertTrue(boundaryForces.get(1).startsWith("0,"));
        assertTrue(boundaryForces.get(2).startsWith("2,"));
    }

    private System2OutputMetadata metadata() {
        return new System2OutputMetadata(
                "run-1",
                0,
                new System2Config(geometry, 1, 1.0, 1.0, 100.0, 0.1, 1, 1234L),
                "velocity_verlet",
                1,
                1
        );
    }
}
