package ar.edu.itba.sds.tp4.system2.runner;

import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.model.System2Geometry;
import ar.edu.itba.sds.tp4.system2.output.System2CsvSnapshotSink;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class System2RunnerTest {
    @TempDir
    Path outputDirectory;

    @Test
    void runnerConnectsInitializationEngineAndRawWriters() throws Exception {
        System2Config config = new System2Config(
                new System2Geometry(80.0, 1.0, 1.0),
                5,
                1.0,
                1.0,
                100.0,
                0.01,
                2,
                1234L
        );
        System2RunRequest request = new System2RunRequest("test-run", 0, config, outputDirectory);

        System2RunnerResult result = new System2Runner().run(request);

        assertEquals(outputDirectory, result.outputDirectory());
        assertEquals(2, result.runResult().stepsExecuted());
        assertEquals(3, result.runResult().snapshotsWritten());
        assertEquals(2, result.runResult().finalState().step());
        assertEquals(0.02, result.runResult().finalState().time(), 1e-12);

        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.METADATA_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.STATES_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.CONTACTS_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.CONTACT_EVENTS_FILE_NAME)));
        assertTrue(Files.exists(outputDirectory.resolve(System2CsvSnapshotSink.BOUNDARY_FORCES_FILE_NAME)));

        List<String> states = Files.readAllLines(outputDirectory.resolve(System2CsvSnapshotSink.STATES_FILE_NAME));
        List<String> boundaryForces = Files.readAllLines(
                outputDirectory.resolve(System2CsvSnapshotSink.BOUNDARY_FORCES_FILE_NAME)
        );
        String metadata = Files.readString(outputDirectory.resolve(System2CsvSnapshotSink.METADATA_FILE_NAME));

        assertEquals(1 + config.particleCount() * (config.steps() + 1), states.size());
        assertEquals(1 + config.steps() + 1, boundaryForces.size());
        assertTrue(metadata.contains("\"run_id\": \"test-run\""));
        assertTrue(metadata.contains("\"integrator\": \"velocity_verlet\""));
    }
}
