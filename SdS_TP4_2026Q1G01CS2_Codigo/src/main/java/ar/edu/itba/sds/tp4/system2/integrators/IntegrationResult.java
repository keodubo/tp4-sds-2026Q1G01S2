package ar.edu.itba.sds.tp4.system2.integrators;

import ar.edu.itba.sds.tp4.system2.forces.ForceEvaluation;
import ar.edu.itba.sds.tp4.system2.state.System2State;

public record IntegrationResult(
        System2State initialState,
        ForceEvaluation initialForces,
        System2State nextState,
        ForceEvaluation nextForces
) {
    public IntegrationResult {
        if (initialState == null) {
            throw new IllegalArgumentException("initialState must not be null.");
        }
        if (initialForces == null) {
            throw new IllegalArgumentException("initialForces must not be null.");
        }
        if (nextState == null) {
            throw new IllegalArgumentException("nextState must not be null.");
        }
        if (nextForces == null) {
            throw new IllegalArgumentException("nextForces must not be null.");
        }
    }
}
