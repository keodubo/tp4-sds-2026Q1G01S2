package ar.edu.itba.sds.tp4.system2.engine;

import ar.edu.itba.sds.tp4.system2.state.System2State;

public record System2RunResult(System2State finalState, long stepsExecuted, long snapshotsWritten) {
    public System2RunResult {
        if (finalState == null) {
            throw new IllegalArgumentException("finalState must not be null.");
        }
        if (stepsExecuted < 0) {
            throw new IllegalArgumentException("stepsExecuted must be non-negative.");
        }
        if (snapshotsWritten < 0) {
            throw new IllegalArgumentException("snapshotsWritten must be non-negative.");
        }
    }
}
