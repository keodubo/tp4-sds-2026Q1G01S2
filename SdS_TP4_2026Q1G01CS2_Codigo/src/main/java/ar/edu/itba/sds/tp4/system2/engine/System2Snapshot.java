package ar.edu.itba.sds.tp4.system2.engine;

import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluation;
import ar.edu.itba.sds.tp4.system2.state.System2State;

public record System2Snapshot(System2State state, ForceEvaluation forces) {
    public System2Snapshot {
        if (state == null) {
            throw new IllegalArgumentException("state must not be null.");
        }
        if (forces == null) {
            throw new IllegalArgumentException("forces must not be null.");
        }
    }
}
