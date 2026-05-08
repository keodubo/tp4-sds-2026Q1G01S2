package ar.edu.itba.sds.tp4.system2.forces;

import ar.edu.itba.sds.tp4.system2.state.System2State;

public interface ForceEvaluator {
    ForceEvaluation evaluate(System2State state);
}
