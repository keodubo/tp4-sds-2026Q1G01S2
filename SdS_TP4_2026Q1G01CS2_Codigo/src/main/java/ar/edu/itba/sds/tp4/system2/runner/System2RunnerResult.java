package ar.edu.itba.sds.tp4.system2.runner;

import ar.edu.itba.sds.tp4.system2.engine.System2RunResult;

import java.nio.file.Path;

public record System2RunnerResult(Path outputDirectory, System2RunResult runResult) {
    public System2RunnerResult {
        if (outputDirectory == null) {
            throw new IllegalArgumentException("outputDirectory must not be null.");
        }
        if (runResult == null) {
            throw new IllegalArgumentException("runResult must not be null.");
        }
    }
}
