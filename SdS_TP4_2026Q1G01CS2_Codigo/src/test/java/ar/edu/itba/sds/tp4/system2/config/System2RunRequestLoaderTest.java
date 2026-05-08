package ar.edu.itba.sds.tp4.system2.config;

import ar.edu.itba.sds.tp4.system2.runner.System2RunRequest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class System2RunRequestLoaderTest {
    @TempDir
    Path tempDirectory;

    @Test
    void loadsSystem2RunRequestFromTomlFile() throws Exception {
        Path configPath = tempDirectory.resolve("system2.toml");
        Files.writeString(configPath, """
                [run]
                run_id = "run-a"
                realization = 2
                output_dir = "outputs/run-a"

                [geometry]
                diameter = 80.0
                obstacle_radius = 1.0
                particle_radius = 1.0

                [particles]
                count = 100
                mass = 1.0
                initial_speed = 1.0

                [interaction]
                k = 10000.0

                [simulation]
                dt = 0.0001
                steps = 500
                seed = 12345
                """);

        System2RunRequest request = new System2RunRequestLoader().load(configPath);

        assertEquals("run-a", request.runId());
        assertEquals(2, request.realization());
        assertEquals(tempDirectory.resolve("outputs/run-a").normalize(), request.outputDirectory());
        assertEquals(100, request.config().particleCount());
        assertEquals(80.0, request.config().geometry().diameter(), 1e-12);
        assertEquals(40.0, request.config().geometry().outerRadius(), 1e-12);
        assertEquals(10000.0, request.config().stiffness(), 1e-12);
        assertEquals(0.0001, request.config().dt(), 1e-12);
        assertEquals(500, request.config().steps());
        assertEquals(12345L, request.config().seed());
    }

    @Test
    void rejectsMissingRequiredTables() throws Exception {
        Path configPath = tempDirectory.resolve("invalid.toml");
        Files.writeString(configPath, """
                [run]
                run_id = "bad"
                realization = 0
                output_dir = "outputs/bad"
                """);

        assertThrows(IllegalArgumentException.class, () -> new System2RunRequestLoader().load(configPath));
    }
}
