package ar.edu.itba.sds.tp4.system2.runner;

import ar.edu.itba.sds.tp4.system2.model.System2Config;
import ar.edu.itba.sds.tp4.system2.output.System2OutputConfig;

import java.nio.file.Path;

public record System2RunRequest(
        String runId,
        int realization,
        System2Config config,
        Path outputDirectory,
        System2OutputConfig outputConfig
) {
    public System2RunRequest(String runId, int realization, System2Config config, Path outputDirectory) {
        this(runId, realization, config, outputDirectory, System2OutputConfig.fullResolution());
    }

    public System2RunRequest {
        if (runId == null || runId.isBlank()) {
            throw new IllegalArgumentException("runId must not be blank.");
        }
        if (realization < 0) {
            throw new IllegalArgumentException("realization must be non-negative.");
        }
        if (config == null) {
            throw new IllegalArgumentException("config must not be null.");
        }
        if (outputDirectory == null) {
            throw new IllegalArgumentException("outputDirectory must not be null.");
        }
        if (outputConfig == null) {
            throw new IllegalArgumentException("outputConfig must not be null.");
        }
    }
}
